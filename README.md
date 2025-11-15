# ContextIQ - Local AI Meeting Assistant

A local AI system that answers natural language questions about team meetings and chat transcripts using RAG (Retrieval Augmented Generation) with ChromaDB and LM Studio.

## 🏗️ Architecture

### 1. MCP Layer (Controller Logic)
- **Location**: `mcp/ingest.py`, `mcp/server.py`
- Reads `.txt` transcripts from `data/transcripts/`
- Splits transcripts into chunks with overlap
- Creates embeddings using sentence-transformers
- Stores embeddings in ChromaDB
- Tracks processed files by hash (no duplicate ingestion)
- Maintains metadata (filename, date, chunk_id)

### 2. RAG System (ChromaDB)
- **Location**: `mcp/rag.py`
- Persistent vector database stored in `mcp/db/chroma/`
- Similarity search for relevant chunks
- Never overwrites old data (preserves history)
- Returns ranked results with metadata

### 3. Local LLM (LM Studio)
- **Location**: `mcp/llm.py`
- Integrates with Phi-3, LLaMA 3, or other models via LM Studio
- Uses OpenAI-compatible API
- Generates answers based only on provided context
- No external memory or web access

## 📁 Project Structure

```
contextiq/
├── data/
│   └── transcripts/          # Place your .txt transcript files here
├── mcp/
│   ├── __init__.py           # Package initialization
│   ├── config.py             # Configuration management
│   ├── ingest.py             # Transcript ingestion & chunking
│   ├── rag.py                # ChromaDB RAG system
│   ├── llm.py                # LM Studio integration
│   ├── server.py             # FastAPI server with MCP endpoints
│   └── db/
│       ├── chroma/           # ChromaDB persistent storage
│       └── processed_files.json  # Ingestion tracking
├── ui/
│   └── brainwave/            # (Future UI - not required)
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
└── README.md                 # This file
```

## 🚀 Setup & Installation

### Prerequisites
- Python 3.10 or higher
- [LM Studio](https://lmstudio.ai/) installed and running
- A model loaded in LM Studio (Phi-3, LLaMA 3, etc.)

### Installation Steps

1. **Clone or navigate to the project directory**
   ```bash
   cd c:\Users\sarva\Desktop\nf\code\Kmit25\contextiq
   ```

2. **Create a virtual environment** (recommended)
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```powershell
   Copy-Item .env.example .env
   # Edit .env if needed (default values work for standard LM Studio setup)
   ```

5. **Start LM Studio**
   - Open LM Studio
   - Load your preferred model (e.g., Phi-3, LLaMA 3)
   - Enable the local server (default: http://localhost:1234)

## 📝 Usage

### 1. Add Transcript Files

Place your `.txt` transcript files in `data/transcripts/`:

```
data/transcripts/
├── meeting-2024-01-15.txt
├── standup-2024-01-16.txt
└── chat-log-2024-01-17.txt
```

### 2. Start the MCP Server

```powershell
python -m mcp.server
```

Or use uvicorn directly:
```powershell
uvicorn mcp.server:app --reload --host 0.0.0.0 --port 8000
```

The server will:
- Auto-ingest new transcripts on startup
- Create embeddings and store in ChromaDB
- Start the API on http://localhost:8000

### 3. Ask Questions

#### Via API (curl/Postman)

```powershell
# Ask a question
curl -X POST "http://localhost:8000/ask" `
  -H "Content-Type: application/json" `
  -d '{"question": "What tasks were assigned in the last meeting?"}'

# Trigger manual ingestion
curl -X POST "http://localhost:8000/ingest"

# Check system status
curl "http://localhost:8000/status"
```

#### Via Python

```python
import requests

response = requests.post(
    "http://localhost:8000/ask",
    json={
        "question": "What did we discuss about the project timeline?",
        "n_results": 5,
        "include_sources": True
    }
)

print(response.json()["answer"])
```

### 4. MCP Integration with LM Studio

The server provides MCP-compatible endpoints for direct integration:

- `GET /tools` - List available MCP tools
- `POST /tools/search_transcripts` - Search transcripts
- `POST /tools/ask_about_transcripts` - Ask questions

To connect from LM Studio:
1. Configure MCP server URL: `http://localhost:8000`
2. Use the tool endpoints to query transcripts

## 🔧 API Endpoints

### Main Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information |
| `/ask` | POST | Ask a question about transcripts |
| `/ingest` | POST | Manually trigger transcript ingestion |
| `/status` | GET | Get system status |
| `/health` | GET | Health check |
| `/docs` | GET | Interactive API documentation |

### MCP Tool Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/tools` | GET | List available MCP tools |
| `/tools/search_transcripts` | POST | Search transcripts (MCP tool) |
| `/tools/ask_about_transcripts` | POST | Ask questions (MCP tool) |

## 🎯 Features

✅ **Incremental Ingestion**: Only processes new or modified transcripts  
✅ **Persistent Storage**: Embeddings persist between restarts  
✅ **Metadata Tracking**: Preserves filename, date, chunk information  
✅ **Historical Data**: Never overwrites old chunks  
✅ **Source Citation**: Returns which transcripts were used for answers  
✅ **MCP Protocol**: Compatible with LM Studio MCP integration  
✅ **Auto-ingestion**: Processes new transcripts on startup  
✅ **FastAPI**: Modern, fast API with auto-documentation  

## ⚙️ Configuration

Edit `.env` to customize:

```env
# LM Studio
LM_STUDIO_BASE_URL=http://localhost:1234/v1
LM_STUDIO_MODEL=local-model

# RAG Settings
EMBEDDING_MODEL=all-MiniLM-L6-v2
DEFAULT_N_RESULTS=5

# Chunking
CHUNK_SIZE=500
CHUNK_OVERLAP=50
```

## 🧪 Testing

```powershell
# Check if server is running
curl http://localhost:8000/health

# Check system status
curl http://localhost:8000/status

# Test with a question
curl -X POST "http://localhost:8000/ask" `
  -H "Content-Type: application/json" `
  -d '{"question": "Hello, can you read transcripts?"}'
```

## 📊 How It Works

1. **Ingestion Phase**:
   - Scans `data/transcripts/` for `.txt` files
   - Calculates file hash to detect changes
   - Splits text into ~500 word chunks with 50 word overlap
   - Generates embeddings using `all-MiniLM-L6-v2`
   - Stores in ChromaDB with metadata

2. **Query Phase**:
   - User asks a question via `/ask` endpoint
   - Question is embedded using same model
   - ChromaDB finds top-5 most similar chunks
   - Chunks are formatted with metadata
   - Context + question sent to LM Studio
   - LLM generates answer based on context

3. **Response**:
   - Returns AI-generated answer
   - Includes source files and dates
   - Optionally includes full context used

## 🔍 Troubleshooting

**LM Studio Connection Issues**:
- Ensure LM Studio is running
- Check server is on http://localhost:1234
- Verify a model is loaded

**No Transcripts Found**:
- Check files are in `data/transcripts/`
- Ensure files have `.txt` extension
- Check file permissions

**Poor Answer Quality**:
- Increase `n_results` to retrieve more context
- Adjust `CHUNK_SIZE` for better granularity
- Try a different LM Studio model

## 📚 Dependencies

- **FastAPI**: Modern web framework
- **ChromaDB**: Vector database
- **sentence-transformers**: Embedding generation
- **OpenAI**: LM Studio API client
- **Pydantic**: Data validation
- **Uvicorn**: ASGI server

## 🛣️ Roadmap

- [ ] Web UI (Brainwave integration)
- [ ] Support for PDF/DOCX transcripts
- [ ] Multi-collection support
- [ ] Advanced filtering by date/source
- [ ] Conversation history
- [ ] Export answers to markdown

## 📄 License

MIT License - Feel free to use and modify!

## 👥 Contributing

This is a personal project, but suggestions are welcome!

---

**Built with ❤️ using Claude 4 in VS Code**
