"""
LLM Integration Module
Handles communication with LM Studio using OpenAI-compatible API
"""
from openai import OpenAI
from typing import Optional, Dict, List
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LMStudioClient:
    """Client for interacting with LM Studio's OpenAI-compatible API"""
    
    def __init__(self, 
                 base_url: str = "http://localhost:1234/v1",
                 api_key: str = "lm-studio",
                 model: str = "local-model",
                 temperature: float = 0.7,
                 max_tokens: int = 2048):
        """
        Initialize LM Studio client
        
        Args:
            base_url: LM Studio API base URL
            api_key: API key (default works for LM Studio)
            model: Model identifier (use "local-model" or check LM Studio)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens in response
        """
        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Initialize OpenAI client pointing to LM Studio
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )
        
        logger.info(f"LM Studio client initialized - URL: {base_url}, Model: {model}")
    
    def generate_response(self, 
                         prompt: str,
                         system_prompt: Optional[str] = None,
                         temperature: Optional[float] = None,
                         max_tokens: Optional[int] = None) -> str:
        """
        Generate a response from the LLM
        
        Args:
            prompt: User prompt/question
            system_prompt: Optional system prompt for context
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            
        Returns:
            Generated response text
        """
        messages = []
        
        # Add system prompt if provided
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        # Add user prompt
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        try:
            # Call LM Studio API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
            )
            
            # Extract response text
            answer = response.choices[0].message.content
            logger.info(f"Generated response ({len(answer)} chars)")
            
            return answer
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise
    
    def answer_with_context(self, 
                           question: str,
                           context: str,
                           custom_system_prompt: Optional[str] = None) -> str:
        """
        Answer a question using provided context (RAG pattern)
        
        Args:
            question: User's question
            context: Retrieved context from RAG system
            custom_system_prompt: Optional custom system prompt
            
        Returns:
            Generated answer
        """
        # Default system prompt for RAG
        default_system_prompt = """You are a helpful AI assistant that answers questions based on meeting transcripts and chat logs.

Your task is to:
1. Carefully read the provided context from transcript chunks
2. Answer the user's question based ONLY on the information in the context
3. If the context doesn't contain enough information, say so clearly
4. Cite which source/date the information comes from when possible
5. Be concise but comprehensive
6. If you notice contradictions or changes over time in the context, point them out

Remember: Do not use external knowledge. Only use the provided context."""

        system_prompt = custom_system_prompt or default_system_prompt
        
        # Build the full prompt with context
        full_prompt = f"""Context from transcripts:

{context}

---

Question: {question}

Please answer the question based on the context provided above."""
        
        return self.generate_response(
            prompt=full_prompt,
            system_prompt=system_prompt
        )
    
    def test_connection(self) -> bool:
        """
        Test connection to LM Studio
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = self.generate_response(
                prompt="Hello! Please respond with 'OK' if you can read this.",
                max_tokens=50
            )
            logger.info(f"Connection test successful. Response: {response[:100]}")
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """
        Get list of available models from LM Studio
        
        Returns:
            List of model names
        """
        try:
            models = self.client.models.list()
            model_names = [model.id for model in models.data]
            logger.info(f"Available models: {model_names}")
            return model_names
        except Exception as e:
            logger.error(f"Error fetching models: {e}")
            return []


# Utility functions
def create_llm_client(base_url: str = "http://localhost:1234/v1") -> LMStudioClient:
    """
    Create and return an LM Studio client
    
    Args:
        base_url: LM Studio API base URL
        
    Returns:
        LMStudioClient instance
    """
    return LMStudioClient(base_url=base_url)


def ask_llm(question: str, 
            context: str,
            client: Optional[LMStudioClient] = None) -> str:
    """
    Ask a question with context using LM Studio
    
    Args:
        question: User's question
        context: Retrieved context
        client: Optional LMStudioClient instance
        
    Returns:
        Generated answer
    """
    if client is None:
        client = create_llm_client()
    
    return client.answer_with_context(question, context)
