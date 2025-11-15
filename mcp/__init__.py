"""
MCP Package - ContextIQ
Local AI system for answering questions about transcripts
"""
from mcp.ingest import TranscriptIngestor, ingest_transcripts
from mcp.rag import RAGSystem, create_rag_system, search_transcripts
from mcp.llm import LMStudioClient, create_llm_client, ask_llm
from mcp.config import settings, get_settings

__version__ = "1.0.0"
__all__ = [
    "TranscriptIngestor",
    "ingest_transcripts",
    "RAGSystem", 
    "create_rag_system",
    "search_transcripts",
    "LMStudioClient",
    "create_llm_client",
    "ask_llm",
    "settings",
    "get_settings"
]
