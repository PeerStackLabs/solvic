import asyncio
import chromadb
from chromadb.config import Settings
from pathlib import Path
import json
from mcp.server import Server
from mcp.types import Tool, TextContent, CallToolResult
from mcp.server.stdio import stdio_server

TRANSCRIPTS_DIR = Path(__file__).parent.parent / "data" / "transcripts"
CHROMA_DB_PATH = Path(__file__).parent / "chroma_db"

class TranscriptRAGServer:
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=str(CHROMA_DB_PATH),
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = None
        self.initialized = False

    def initialize_db(self):
        if self.initialized:
            return
        
        try:
            self.collection = self.client.get_collection("transcripts")
        except:
            self.collection = self.client.create_collection(
                name="transcripts",
                metadata={"hnsw:space": "cosine"}
            )
            self._load_transcripts()
        
        self.initialized = True

    def _load_transcripts(self):
        if not TRANSCRIPTS_DIR.exists():
            return

        documents = []
        metadatas = []
        ids = []

        for txt_file in TRANSCRIPTS_DIR.glob("*.txt"):
            content = txt_file.read_text(encoding='utf-8')
            chunks = self._chunk_text(content, chunk_size=1000, overlap=200)
            
            for idx, chunk in enumerate(chunks):
                documents.append(chunk)
                metadatas.append({
                    "filename": txt_file.name,
                    "chunk_id": idx
                })
                ids.append(f"{txt_file.stem}_chunk_{idx}")

        if documents:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )

    def _chunk_text(self, text, chunk_size=1000, overlap=200):
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += chunk_size - overlap
        
        return chunks

    def query(self, query_text, n_results=5):
        if not self.initialized:
            self.initialize_db()
        
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        
        return results

    def search_by_filename(self, filename, n_results=10):
        if not self.initialized:
            self.initialize_db()
        
        results = self.collection.get(
            where={"filename": filename},
            limit=n_results
        )
        
        return results

async def main():
    rag_server = TranscriptRAGServer()
    server = Server("transcript-rag")

    @server.list_tools()
    async def list_tools():
        return [
            Tool(
                name="query_transcripts",
                description="Search through meeting transcripts using semantic search. Returns relevant chunks of text.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query to find relevant transcript content"
                        },
                        "n_results": {
                            "type": "integer",
                            "description": "Number of results to return (default: 5)",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="get_transcript",
                description="Retrieve chunks from a specific meeting transcript by filename.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "The transcript filename (e.g., meeting1.txt)"
                        },
                        "n_results": {
                            "type": "integer",
                            "description": "Number of chunks to return (default: 10)",
                            "default": 10
                        }
                    },
                    "required": ["filename"]
                }
            ),
            Tool(
                name="reinitialize_db",
                description="Reload all transcripts into the database. Use this if transcripts have been updated.",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            )
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        if name == "query_transcripts":
            query = arguments.get("query")
            n_results = arguments.get("n_results", 5)
            
            results = rag_server.query(query, n_results)
            
            response_text = f"Found {len(results['documents'][0])} relevant chunks:\n\n"
            for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
                response_text += f"--- Result {i+1} (from {metadata['filename']}) ---\n{doc}\n\n"
            
            return CallToolResult(
                content=[TextContent(type="text", text=response_text)]
            )
        
        elif name == "get_transcript":
            filename = arguments.get("filename")
            n_results = arguments.get("n_results", 10)
            
            results = rag_server.search_by_filename(filename, n_results)
            
            if not results['documents']:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"No chunks found for {filename}")]
                )
            
            response_text = f"Retrieved {len(results['documents'])} chunks from {filename}:\n\n"
            for i, doc in enumerate(results['documents']):
                response_text += f"--- Chunk {i+1} ---\n{doc}\n\n"
            
            return CallToolResult(
                content=[TextContent(type="text", text=response_text)]
            )
        
        elif name == "reinitialize_db":
            rag_server.initialized = False
            if rag_server.collection:
                rag_server.client.delete_collection("transcripts")
            rag_server.initialize_db()
            
            return CallToolResult(
                content=[TextContent(type="text", text="Database reinitialized with all transcripts")]
            )
        
        return CallToolResult(
            content=[TextContent(type="text", text=f"Unknown tool: {name}")]
        )

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
