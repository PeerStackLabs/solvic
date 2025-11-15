# ContextIQ MCP Server - Setup Guide

## Quick Setup (5 minutes)

### Step 1: Install Dependencies
```powershell
# Create virtual environment (optional but recommended)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install packages
pip install -r requirements.txt
```

### Step 2: Configure Environment
```powershell
# Copy environment template
Copy-Item .env.example .env

# Edit .env if needed (defaults work for standard LM Studio)
```

### Step 3: Start LM Studio
1. Open LM Studio application
2. Load a model (Phi-3, LLaMA 3, etc.)
3. Click "Start Server" (should show: http://localhost:1234)

### Step 4: Run Quick Test
```powershell
python quickstart.py
```

This will test:
- ✓ Transcript ingestion
- ✓ ChromaDB setup
- ✓ LM Studio connection
- ✓ End-to-end query

### Step 5: Start the Server
```powershell
python run_server.py
```

Or alternatively:
```powershell
python -m mcp.server
```

Server will start on http://localhost:8000

### Step 6: Test the API

Open browser: http://localhost:8000/docs

Or use curl:
```powershell
# Ask a question
curl -X POST "http://localhost:8000/ask" `
  -H "Content-Type: application/json" `
  -d '{\"question\": \"What action items were assigned?\"}'

# Check status
curl http://localhost:8000/status
```

## Adding Your Own Transcripts

1. Place `.txt` files in `data/transcripts/`
2. Server will auto-ingest on startup, or trigger manually:
```powershell
curl -X POST http://localhost:8000/ingest
```

## Troubleshooting

**"No module named 'mcp'"**
- Make sure you're in the project root directory
- Try: `python -m pip install -e .` (if setup.py exists)

**"Connection refused" to LM Studio**
- Ensure LM Studio is running
- Check it's on http://localhost:1234
- Load a model in LM Studio

**"No documents found"**
- Add .txt files to `data/transcripts/`
- Run: `curl -X POST http://localhost:8000/ingest`

## Project Structure

```
contextiq/
├── data/transcripts/     ← Add your .txt files here
├── mcp/
│   ├── ingest.py        ← Reads & chunks transcripts
│   ├── rag.py           ← ChromaDB vector store
│   ├── llm.py           ← LM Studio integration
│   ├── server.py        ← FastAPI server
│   └── db/chroma/       ← Persistent embeddings
├── requirements.txt
├── run_server.py        ← Easy server startup
└── quickstart.py        ← Test script
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/docs` | GET | Interactive API docs |
| `/ask` | POST | Ask questions |
| `/ingest` | POST | Process new transcripts |
| `/status` | GET | System status |
| `/tools` | GET | MCP tool list |

## MCP Integration

For LM Studio MCP connection:
1. Server URL: `http://localhost:8000`
2. Tools available at `/tools`
3. Use `/tools/ask_about_transcripts` endpoint

## Next Steps

1. Add your transcript files
2. Customize prompts in `mcp/llm.py`
3. Adjust chunk size in `.env`
4. Build a UI (optional)

## Support

Check the main README.md for detailed documentation.
