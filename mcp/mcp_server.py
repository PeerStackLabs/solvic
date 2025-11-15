"""
MCP Server Implementation for LM Studio
Implements the Model Context Protocol for RAG functionality
"""
import asyncio
import sys
import os
from pathlib import Path
from typing import Any, Sequence

# Fix imports - add parent directory to path
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

# Import MCP SDK
import mcp.server as mcp_server
import mcp.types as mcp_types
from mcp.server.stdio import stdio_server as mcp_stdio_server

# Now import our local modules from the mcp package
from mcp.ingest import TranscriptIngestor
from mcp.rag import RAGSystem

# Initialize components
transcript_ingestor = TranscriptIngestor(
    transcripts_dir="data/transcripts",
    metadata_file="mcp/db/processed_files.json"
)

rag_system = RAGSystem(
    persist_directory="mcp/db/chroma",
    collection_name="transcripts"
)

# Create MCP server
app = mcp_server.Server("solvic-rag")

@app.list_resources()
async def list_resources() -> list[mcp_types.Resource]:
    """List available transcript resources"""
    return [
        mcp_types.Resource(
            uri="transcripts://all",
            name="All Transcripts",
            description="Access to all ingested meeting transcripts",
            mimeType="text/plain"
        )
    ]

@app.read_resource()
async def read_resource(uri: str) -> str:
    """Read transcript resource"""
    if uri == "transcripts://all":
        count = rag_system.get_collection_count()
        return f"Total transcript chunks available: {count}"
    return "Resource not found"

@app.list_tools()
async def list_tools() -> list[mcp_types.Tool]:
    """List available tools"""
    return [
        mcp_types.Tool(
            name="search_transcripts",
            description="Search through meeting transcripts to find relevant information",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query or question"
                    },
                    "n_results": {
                        "type": "number",
                        "description": "Number of results to return (default: 5)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        ),
        mcp_types.Tool(
            name="ingest_transcripts",
            description="Ingest new transcript files from the data/transcripts directory",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[mcp_types.TextContent | mcp_types.ImageContent | mcp_types.EmbeddedResource]:
    """Handle tool calls"""
    
    if name == "search_transcripts":
        query = arguments.get("query", "")
        n_results = arguments.get("n_results", 5)
        
        if not query:
            return [mcp_types.TextContent(type="text", text="Error: No query provided")]
        
        try:
            # Search for relevant context
            results = rag_system.search(query, n_results=n_results)
            
            if not results or not results.get('documents') or not results['documents'][0]:
                return [mcp_types.TextContent(
                    type="text",
                    text="No relevant information found in transcripts."
                )]
            
            # Format results
            context_parts = []
            for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0]), 1):
                source = metadata.get('source', 'Unknown')
                context_parts.append(f"[Source {i}: {source}]\n{doc}\n")
            
            context = "\n---\n".join(context_parts)
            
            return [mcp_types.TextContent(
                type="text",
                text=f"Found {len(results['documents'][0])} relevant transcript excerpts:\n\n{context}"
            )]
            
        except Exception as e:
            return [mcp_types.TextContent(
                type="text",
                text=f"Error searching transcripts: {str(e)}"
            )]
    
    elif name == "ingest_transcripts":
        try:
            new_docs = transcript_ingestor.ingest_all_new_transcripts()
            if new_docs:
                added = rag_system.add_documents(new_docs)
                return [mcp_types.TextContent(
                    type="text",
                    text=f"Successfully ingested {added} new transcript chunks"
                )]
            else:
                return [mcp_types.TextContent(
                    type="text",
                    text="No new transcripts to ingest"
                )]
        except Exception as e:
            return [mcp_types.TextContent(
                type="text",
                text=f"Error ingesting transcripts: {str(e)}"
            )]
    
    return [mcp_types.TextContent(type="text", text=f"Unknown tool: {name}")]

async def main():
    """Run the MCP server"""
    async with mcp_stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
