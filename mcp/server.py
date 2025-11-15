"""
MCP Server - Main FastAPI Application
Integrates ingestion, RAG, and LLM for question-answering
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
import uvicorn
import logging
from contextlib import asynccontextmanager

from mcp.ingest import TranscriptIngestor
from mcp.rag import RAGSystem
from mcp.llm import LMStudioClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Global instances
transcript_ingestor: Optional[TranscriptIngestor] = None
rag_system: Optional[RAGSystem] = None
llm_client: Optional[LMStudioClient] = None


# Pydantic models for API
class AskRequest(BaseModel):
    """Request model for /ask endpoint"""
    question: str = Field(..., description="Question to ask about transcripts")
    n_results: int = Field(5, description="Number of context chunks to retrieve", ge=1, le=20)
    include_sources: bool = Field(True, description="Include source information in response")


class AskResponse(BaseModel):
    """Response model for /ask endpoint"""
    answer: str = Field(..., description="Generated answer")
    sources: Optional[List[Dict]] = Field(None, description="Source documents used")
    context_used: Optional[str] = Field(None, description="Context provided to LLM")


class IngestResponse(BaseModel):
    """Response model for /ingest endpoint"""
    message: str
    new_documents_added: int
    total_documents: int


class StatusResponse(BaseModel):
    """Response model for /status endpoint"""
    status: str
    total_documents: int
    lm_studio_connected: bool
    transcripts_directory: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup and shutdown"""
    # Startup
    logger.info("Starting MCP Server...")
    
    global transcript_ingestor, rag_system, llm_client
    
    # Initialize components
    transcript_ingestor = TranscriptIngestor(
        transcripts_dir="data/transcripts",
        metadata_file="mcp/db/processed_files.json"
    )
    
    rag_system = RAGSystem(
        persist_directory="mcp/db/chroma",
        collection_name="transcripts"
    )
    
    llm_client = LMStudioClient(
        base_url="http://localhost:1234/v1",
        model="local-model"
    )
    
    # Auto-ingest on startup
    logger.info("Checking for new transcripts...")
    try:
        new_docs = transcript_ingestor.ingest_all_new_transcripts()
        if new_docs:
            added = rag_system.add_documents(new_docs)
            logger.info(f"Auto-ingestion: Added {added} new document chunks")
    except Exception as e:
        logger.error(f"Error during auto-ingestion: {e}")
    
    # Test LM Studio connection
    try:
        if llm_client.test_connection():
            logger.info("LM Studio connection successful")
        else:
            logger.warning("LM Studio connection failed - check if LM Studio is running")
    except Exception as e:
        logger.warning(f"Could not connect to LM Studio: {e}")
    
    logger.info("MCP Server ready!")
    
    yield
    
    # Shutdown
    logger.info("Shutting down MCP Server...")


# Create FastAPI app
app = FastAPI(
    title="ContextIQ MCP Server",
    description="Local AI system for answering questions about meeting transcripts",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "ContextIQ MCP Server",
        "version": "1.0.0",
        "endpoints": {
            "/ask": "Ask questions about transcripts",
            "/ingest": "Manually trigger transcript ingestion",
            "/status": "Get system status",
            "/docs": "API documentation"
        }
    }


@app.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest) -> AskResponse:
    """
    Ask a question about the transcripts
    
    This endpoint:
    1. Retrieves relevant context chunks from the RAG system
    2. Builds a prompt with the context
    3. Sends to LM Studio for answer generation
    4. Returns the answer with optional source information
    """
    try:
        # Query RAG system for relevant context
        logger.info(f"Query: {request.question}")
        results = rag_system.query(
            query_text=request.question,
            n_results=request.n_results
        )
        
        if not results["documents"]:
            return AskResponse(
                answer="I couldn't find any relevant information in the transcripts to answer your question.",
                sources=[],
                context_used=""
            )
        
        # Build context from results
        context = rag_system.build_context_from_results(results, max_chunks=request.n_results)
        logger.info(f"Retrieved {len(results['documents'])} context chunks")
        
        # Generate answer using LLM
        answer = llm_client.answer_with_context(
            question=request.question,
            context=context
        )
        
        # Prepare sources if requested
        sources = None
        if request.include_sources:
            sources = [
                {
                    "filename": meta.get("filename"),
                    "date": meta.get("date"),
                    "chunk_id": meta.get("chunk_id"),
                    "relevance_score": 1 - dist  # Convert distance to similarity
                }
                for meta, dist in zip(results["metadatas"], results["distances"])
            ]
        
        return AskResponse(
            answer=answer,
            sources=sources,
            context_used=context if request.include_sources else None
        )
        
    except Exception as e:
        logger.error(f"Error in /ask endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest", response_model=IngestResponse)
async def ingest_transcripts() -> IngestResponse:
    """
    Manually trigger transcript ingestion
    
    Checks for new or modified transcripts and adds them to the database
    """
    try:
        logger.info("Manual ingestion triggered")
        
        # Ingest new transcripts
        new_docs = transcript_ingestor.ingest_all_new_transcripts()
        
        # Add to RAG system
        added = 0
        if new_docs:
            added = rag_system.add_documents(new_docs)
        
        # Get total count
        stats = rag_system.get_collection_stats()
        total = stats.get("total_documents", 0)
        
        return IngestResponse(
            message=f"Ingestion complete. Added {added} new document chunks.",
            new_documents_added=added,
            total_documents=total
        )
        
    except Exception as e:
        logger.error(f"Error in /ingest endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status", response_model=StatusResponse)
async def get_status() -> StatusResponse:
    """
    Get system status
    
    Returns information about the database, LM Studio connection, etc.
    """
    try:
        # Get RAG stats
        stats = rag_system.get_collection_stats()
        
        # Test LM Studio connection
        lm_studio_ok = False
        try:
            lm_studio_ok = llm_client.test_connection()
        except:
            pass
        
        return StatusResponse(
            status="online",
            total_documents=stats.get("total_documents", 0),
            lm_studio_connected=lm_studio_ok,
            transcripts_directory=str(transcript_ingestor.transcripts_dir)
        )
        
    except Exception as e:
        logger.error(f"Error in /status endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy"}


# MCP Protocol Tools (for LM Studio MCP integration)
@app.get("/tools")
async def list_tools():
    """
    List available MCP tools for LM Studio integration
    
    This endpoint describes the capabilities that can be called via MCP
    """
    return {
        "tools": [
            {
                "name": "search_transcripts",
                "description": "Search meeting transcripts for relevant information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query or question"
                        },
                        "n_results": {
                            "type": "integer",
                            "description": "Number of results to return (default: 5)",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "ask_about_transcripts",
                "description": "Ask a question and get an AI-generated answer based on transcripts",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "The question to ask"
                        }
                    },
                    "required": ["question"]
                }
            }
        ]
    }


@app.post("/tools/search_transcripts")
async def search_transcripts_tool(query: str, n_results: int = 5):
    """MCP tool: Search transcripts"""
    try:
        results = rag_system.query(query_text=query, n_results=n_results)
        context = rag_system.build_context_from_results(results, max_chunks=n_results)
        
        return {
            "success": True,
            "context": context,
            "num_results": len(results["documents"]),
            "sources": [
                {
                    "filename": meta.get("filename"),
                    "date": meta.get("date")
                }
                for meta in results["metadatas"]
            ]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/tools/ask_about_transcripts")
async def ask_about_transcripts_tool(question: str):
    """MCP tool: Ask question about transcripts"""
    try:
        # Use the ask endpoint logic
        request = AskRequest(question=question, n_results=5, include_sources=True)
        response = await ask_question(request)
        
        return {
            "success": True,
            "answer": response.answer,
            "sources": response.sources
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    """Run the server"""
    uvicorn.run(
        "mcp.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()
