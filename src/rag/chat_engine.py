"""
RAG-powered chat engine for meeting transcript queries with guardrails
"""
from typing import List, Dict, Optional
import yaml
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from llm_providers.gemini import GeminiProvider
from rag.vector_store import TranscriptVectorStore
from guardrails.input_guardrails import InputGuardrails, Department, AccessLevel
from guardrails.output_guardrails import OutputGuardrails
from guardrails.user_manager import UserManager, User
from task_managers.notion import NotionTaskManager

class MeetingChatEngine:
    def __init__(self, config_path: str = "config.yml"):
        """Initialize chat engine with RAG capabilities"""
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
        
        # Initialize components
        self.llm = GeminiProvider(self.config['llm_provider'])
        self.vector_store = TranscriptVectorStore()
        
        # Initialize task manager if configured
        self.task_manager = None
        if 'task_manager' in self.config and self.config['task_manager']['type'] == 'notion':
            self.task_manager = NotionTaskManager(self.config['task_manager'])
        
        # Initialize guardrails
        self.input_guardrails = InputGuardrails()
        self.output_guardrails = OutputGuardrails()
        self.user_manager = UserManager()
        
        # Chat history
        self.conversation_history = []
        
        # Audit log
        self.audit_log = []
    
    def index_transcript(self, transcript: Dict) -> bool:
        """Add a transcript to the vector database"""
        return self.vector_store.add_transcript(transcript)
    
    def index_multiple_transcripts(self, transcripts: List[Dict]) -> Dict:
        """Index multiple transcripts"""
        stats = {'added': 0, 'skipped': 0, 'errors': 0}
        
        for transcript in transcripts:
            try:
                if self.vector_store.add_transcript(transcript):
                    stats['added'] += 1
                else:
                    stats['skipped'] += 1
            except Exception as e:
                print(f"Error indexing {transcript.get('title', 'unknown')}: {e}")
                stats['errors'] += 1
        
        return stats
    
    def ask(
        self, 
        question: str, 
        user_id: str,
        n_context_chunks: int = 5
    ) -> Dict:
        """
        Ask a question about meetings using RAG with guardrails
        
        Args:
            question: User question
            user_id: ID of the user asking
            n_context_chunks: Number of relevant chunks to retrieve
        
        Returns:
            Dict with answer, sources, warnings, and metadata
        """
        # Get user
        user = self.user_manager.get_user(user_id)
        if not user:
            return {
                'answer': "⛔ User not found. Please contact administrator.",
                'sources': [],
                'error': 'invalid_user'
            }
        
        # Record query
        self.user_manager.record_query(user_id)
        
        # INPUT GUARDRAILS - Validate query
        input_validation = self.input_guardrails.validate_query(
            question,
            user.department,
            user.access_level
        )
        
        if not input_validation['allowed']:
            # Log blocked query
            self._audit_log('query_blocked', user, question, input_validation['reason'])
            
            return {
                'answer': f"⛔ Query blocked: {input_validation['reason']}",
                'sources': [],
                'warnings': input_validation.get('warnings', []),
                'blocked': True
            }
        
        # Use sanitized query
        sanitized_question = input_validation['sanitized_query']
        warnings = input_validation.get('warnings', [])
        
        # Log query
        self._audit_log('query_submitted', user, question, sanitized_question)
        
        # Retrieve relevant context
        relevant_chunks = self.vector_store.search(sanitized_question, n_results=n_context_chunks)
        
        if not relevant_chunks:
            return {
                'answer': "I don't have any meeting transcripts indexed yet. Please index some transcripts first.",
                'sources': [],
                'confidence': 'low',
                'warnings': [],
                'risk_score': 0.0,
                'sensitivity': 'public'
            }
        
        # Build context from retrieved chunks
        context = self._build_context(relevant_chunks)
        
        # Create prompt
        prompt = self._create_rag_prompt(sanitized_question, context, relevant_chunks)
        
        # Get answer from LLM
        try:
            import google.generativeai as genai
            import os
            api_key = os.getenv('GEMINI_API_KEY')
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = model.generate_content(prompt)
            answer = response.text
        except Exception as e:
            answer = f"Error generating answer: {str(e)}"
        
        # Extract sources
        sources = self._extract_sources(relevant_chunks)
        
        # OUTPUT GUARDRAILS - Filter response
        output_validation = self.output_guardrails.filter_response(
            answer,
            sources,
            user.department,
            user.access_level
        )
        
        # Check if content was blocked
        if output_validation.get('blocked_content'):
            self._audit_log('response_blocked', user, question, 'restricted_content')
        
        # Combine warnings
        all_warnings = warnings + output_validation.get('warnings', [])
        
        # Log redactions
        if output_validation.get('redactions'):
            self._audit_log(
                'content_redacted',
                user,
                question,
                f"Redacted: {output_validation['redactions']}"
            )
        
        # Calculate comprehensive risk score
        risk_score = self._calculate_risk_score(
            question,
            output_validation['filtered_response'],
            input_validation.get('risk_score', 0.0),
            output_validation.get('redactions', []),
            output_validation.get('blocked_content', False)
        )
        
        # Calculate confidence with score details
        confidence_data = self._calculate_confidence_with_score(relevant_chunks)
        
        # Build final response
        final_response = {
            'answer': output_validation['filtered_response'],
            'sources': output_validation['filtered_sources'],
            'confidence': confidence_data['level'],
            'confidence_score': confidence_data['score'],
            'relevant_chunks': len(relevant_chunks),
            'warnings': all_warnings,
            'redactions': output_validation.get('redactions', []),
            'risk_score': risk_score,
            'user': {
                'name': user.name,
                'department': user.department.value,
                'access_level': user.access_level.value
            }
        }
        
        # Add to conversation history
        self.conversation_history.append({
            'user_id': user_id,
            'question': question,
            'sanitized_question': sanitized_question,
            'answer': final_response['answer'],
            'sources': final_response['sources'],
            'timestamp': datetime.now(),
            'warnings': all_warnings
        })
        
        return final_response
    
    def _build_context(self, chunks: List[Dict]) -> str:
        """Build context string from retrieved chunks"""
        context_parts = []
        
        for i, chunk in enumerate(chunks, 1):
            metadata = chunk['metadata']
            content = chunk['content']
            
            context_parts.append(
                f"[Source {i}]\n"
                f"Meeting: {metadata.get('title', 'Unknown')}\n"
                f"Date: {metadata.get('timestamp', 'Unknown')}\n"
                f"Content:\n{content}\n"
            )
        
        return "\n---\n\n".join(context_parts)
    
    def _create_rag_prompt(self, question: str, context: str, chunks: List[Dict]) -> str:
        """Create RAG prompt for the LLM"""
        return f"""You are an AI assistant helping users understand their meeting transcripts.

CONTEXT FROM RELEVANT MEETINGS:
{context}

USER QUESTION:
{question}

INSTRUCTIONS:
1. Answer the question based ONLY on the context provided above
2. If the context doesn't contain enough information, say so
3. Cite specific meetings when referencing information
4. Be concise but thorough
5. If dates or deadlines are mentioned, include them
6. If action items or decisions are discussed, highlight them

ANSWER:"""
    
    def _extract_sources(self, chunks: List[Dict]) -> List[Dict]:
        """Extract unique source meetings from chunks"""
        sources = {}
        
        for chunk in chunks:
            metadata = chunk['metadata']
            parent_id = metadata.get('parent_id', '')
            
            if parent_id not in sources:
                sources[parent_id] = {
                    'title': metadata.get('title', 'Unknown'),
                    'timestamp': metadata.get('timestamp', 'Unknown'),
                    'source': metadata.get('source', 'Unknown')
                }
        
        return list(sources.values())
    
    def _estimate_confidence(self, chunks: List[Dict]) -> str:
        """
        Estimate confidence based on retrieval distances and result quality
        
        ChromaDB uses cosine distance: lower is better (0 = perfect match, 2 = opposite)
        Typical ranges:
        - 0.0 - 0.3: Excellent match
        - 0.3 - 0.6: Good match  
        - 0.6 - 1.0: Fair match
        - 1.0+: Poor match
        """
        if not chunks:
            return 'none'
        
        # Calculate average distance (lower is better)
        avg_distance = sum(c['distance'] for c in chunks) / len(chunks)
        
        # Get minimum distance (best match)
        min_distance = min(c['distance'] for c in chunks)
        
        # Consider both average and best match for confidence
        # Weight best match more heavily (60/40 split)
        weighted_score = (min_distance * 0.6) + (avg_distance * 0.4)
        
        # More granular thresholds based on actual ChromaDB performance
        if weighted_score <= 0.4:
            return 'high'      # Excellent semantic match
        elif weighted_score <= 0.7:
            return 'medium'    # Good match with some uncertainty
        elif weighted_score <= 1.0:
            return 'low'       # Weak match, may not be relevant
        else:
            return 'none'      # Very poor match, likely irrelevant
    
    def _calculate_confidence_with_score(self, chunks: List[Dict]) -> Dict:
        """
        Calculate confidence level and provide numeric score for display
        
        Returns dict with 'level' (high/medium/low/none) and 'score' (0-100)
        """
        if not chunks:
            return {'level': 'none', 'score': 0}
        
        # Calculate distances
        avg_distance = sum(c['distance'] for c in chunks) / len(chunks)
        min_distance = min(c['distance'] for c in chunks)
        weighted_score = (min_distance * 0.6) + (avg_distance * 0.4)
        
        # Convert distance to confidence percentage (inverse relationship)
        # Distance 0.0 = 100% confidence, Distance 1.0+ = 0% confidence
        confidence_percent = max(0, min(100, (1.0 - weighted_score) * 100))
        
        # Determine level
        if weighted_score <= 0.4:
            level = 'high'
        elif weighted_score <= 0.7:
            level = 'medium'
        elif weighted_score <= 1.0:
            level = 'low'
        else:
            level = 'none'
        
        return {
            'level': level,
            'score': round(confidence_percent, 1)
        }
    
    def _calculate_risk_score(
        self,
        query: str,
        response: str,
        input_risk: float,
        redactions: List[Dict],
        blocked: bool
    ) -> float:
        """Calculate comprehensive risk score based on query and response"""
        import re
        
        risk_score = input_risk
        
        # Critical: Content was blocked
        if blocked:
            return 1.0
        
        # High risk: Redactions occurred (increased weight)
        if redactions:
            risk_score += 0.5 * len(redactions)  # Increased from 0.3 to 0.5
        
        # Check for sensitive content in response (increased weight)
        sensitive_patterns = {
            'financial': r'\$\d{1,3}(,\d{3})*(\.\d{2})?',
            'salary': r'salary|compensation|pay\s*grade|bonus',
            'hr_sensitive': r'layoff|termination|firing|dismissed',
            'confidential': r'confidential|proprietary|trade\s*secret|NDA',
            'personal': r'password|credential|access\s*code',
        }
        
        for pattern_name, pattern in sensitive_patterns.items():
            if re.search(pattern, response, re.IGNORECASE):
                risk_score += 0.25  # Increased from 0.15 to 0.25
        
        # Check for PII patterns still present (shouldn't happen after redaction) (increased weight)
        pii_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # Phone
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
        ]
        
        for pattern in pii_patterns:
            if re.search(pattern, response):
                risk_score += 0.4  # Increased from 0.25 to 0.4 - High risk if PII leaked through
        
        # Long responses with sensitive keywords
        if len(response) > 1500:
            sensitive_keywords = ['confidential', 'restricted', 'internal only', 'do not share']
            if any(kw in response.lower() for kw in sensitive_keywords):
                risk_score += 0.1
        
        # Warning indicators
        if any(word in response.lower() for word in ['warning', 'caution', 'sensitive', 'restricted']):
            risk_score += 0.05
        
        # Normalize to 0-100 percentage range
        return min(round(risk_score * 100, 1), 100.0)
    
    def _audit_log(self, event_type: str, user: User, query: str, details: str):
        """Log security/audit events"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'user_id': user.user_id,
            'user_name': user.name,
            'department': user.department.value,
            'access_level': user.access_level.value,
            'query': query,
            'details': details
        }
        
        self.audit_log.append(log_entry)
        
        # Write to file for persistence
        import json
        from pathlib import Path
        
        audit_file = Path("./data/audit.log")
        audit_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(audit_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def get_audit_logs(self, user_id: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get audit logs, optionally filtered by user"""
        logs = self.audit_log[-limit:]
        
        if user_id:
            logs = [log for log in logs if log['user_id'] == user_id]
        
        return logs
    
    def get_conversation_history(self) -> List[Dict]:
        """Get chat history"""
        return self.conversation_history
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
    
    def get_stats(self) -> Dict:
        """Get system statistics"""
        return {
            **self.vector_store.get_stats(),
            'conversation_turns': len(self.conversation_history)
        }
    
    def create_task(self, task_name: str, assignee: str = None, due_date: str = None, notes: str = None) -> Dict:
        """
        Create a task in Notion
        
        Args:
            task_name: Task description
            assignee: Person to assign the task to
            due_date: Due date in YYYY-MM-DD format
            notes: Additional task notes
        
        Returns:
            Dict with success status and message
        """
        if not self.task_manager:
            return {
                'success': False,
                'message': 'Task manager not configured. Please set up Notion integration in config.yml'
            }
        
        try:
            from dataclasses import dataclass
            from datetime import datetime as dt
            
            # Create a simple task object
            @dataclass
            class Task:
                name: str
                notes: str = ""
                due_date: str = None
            
            # Build notes field with assignee
            task_notes = ""
            if assignee:
                task_notes = f"Assigned to: {assignee}\n\n"
            if notes:
                task_notes += notes
            if due_date:
                task_notes += f"\n\nDue: {due_date}"
            
            task = Task(
                name=task_name,
                notes=task_notes.strip(),
                due_date=due_date
            )
            
            self.task_manager.create_task(task)
            
            return {
                'success': True,
                'message': f'✅ Task created: {task_name}'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'❌ Failed to create task: {str(e)}'
            }
