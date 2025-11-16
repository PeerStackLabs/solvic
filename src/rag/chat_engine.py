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

class MeetingChatEngine:
    def __init__(self, config_path: str = "config.yml"):
        """Initialize chat engine with RAG capabilities"""
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
        
        # Initialize components
        self.llm = GeminiProvider(self.config['llm_provider'])
        self.vector_store = TranscriptVectorStore()
        
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
        
        # Build final response
        final_response = {
            'answer': output_validation['filtered_response'],
            'sources': output_validation['filtered_sources'],
            'confidence': self._estimate_confidence(relevant_chunks),
            'relevant_chunks': len(relevant_chunks),
            'warnings': all_warnings,
            'redactions': output_validation.get('redactions', []),
            'risk_score': input_validation.get('risk_score', 0.0),
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
        """Estimate confidence based on retrieval distances"""
        if not chunks:
            return 'none'
        
        avg_distance = sum(c['distance'] for c in chunks) / len(chunks)
        
        if avg_distance < 0.3:
            return 'high'
        elif avg_distance < 0.5:
            return 'medium'
        else:
            return 'low'
    
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
