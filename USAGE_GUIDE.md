# 🎯 ContextIQ - Complete Usage Guide

## Table of Contents
1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [API Usage](#api-usage)
4. [Python Client](#python-client)
5. [MCP Integration](#mcp-integration)
6. [Configuration](#configuration)
7. [Examples](#examples)

---

## Installation

### Step 1: Install Python Dependencies

```powershell
# Navigate to project directory
cd c:\Users\sarva\Desktop\nf\code\Kmit25\contextiq

# Create virtual environment (recommended)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

**Expected output:**
```
Successfully installed fastapi-0.109.0 chromadb-0.4.22 ...
```

### Step 2: Configure Environment (Optional)

```powershell
# Copy environment template
Copy-Item .env.example .env

# Edit .env with your preferred settings (optional)
notepad .env
```

Default settings work for standard LM Studio installation.

### Step 3: Set Up LM Studio

1. **Download and Install**: [https://lmstudio.ai/](https://lmstudio.ai/)
2. **Download a Model**:
   - Recommended: `Phi-3-mini-4k-instruct` (fast, good quality)
   - Alternative: `Meta-Llama-3-8B-Instruct` (slower, better quality)
3. **Start Local Server**:
   - Click "Local Server" tab
   - Click "Start Server"
   - Verify it shows: `Server running on http://localhost:1234`

### Step 4: Verify Installation

```powershell
python quickstart.py
```

**Expected output:**
```
============================================================
ContextIQ Quick Start Test
============================================================

1. Testing Transcript Ingestor...
   ✓ Found 2 new transcript(s)
   ✓ Created 8 chunks

2. Testing RAG System (ChromaDB)...
   ✓ ChromaDB initialized
   ✓ Total documents: 8
   ✓ Added 8 new documents to RAG

3. Testing LM Studio Connection...
   ✓ LM Studio connected
   ✓ Available models: local-model
   ✓ Response: OK

4. Testing End-to-End Query...
   ✓ Found 3 relevant chunks
   ✓ Generated answer (245 chars)
```

---

## Quick Start

### Start the Server

```powershell
python run_server.py
```

**Output:**
```
============================================================
Starting ContextIQ MCP Server
============================================================
Server: http://0.0.0.0:8000
Docs:   http://localhost:8000/docs
LM Studio: http://localhost:1234/v1
============================================================

INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Checking for new transcripts...
INFO:     Processing 2 new/modified transcript(s)
INFO:     Added 8 new document chunks
INFO:     LM Studio connection successful
INFO:     MCP Server ready!
```

### Test the Server

**Option 1: Browser**
- Open: http://localhost:8000/docs
- Try the interactive API documentation

**Option 2: PowerShell**
```powershell
curl http://localhost:8000/status
```

**Expected response:**
```json
{
  "status": "online",
  "total_documents": 8,
  "lm_studio_connected": true,
  "transcripts_directory": "data\\transcripts"
}
```

---

## API Usage

### 1. Ask Questions

**PowerShell:**
```powershell
$body = @{
    question = "What is the MVP deadline?"
    n_results = 5
    include_sources = $true
} | ConvertTo-Json

curl -X POST "http://localhost:8000/ask" `
  -H "Content-Type: application/json" `
  -d $body
```

**Response:**
```json
{
  "answer": "Based on the meeting transcript from January 15, 2024, the MVP (Minimum Viable Product) needs to be ready by March 1st. Alice mentioned this timeline during the project kickoff meeting.",
  "sources": [
    {
      "filename": "meeting-2024-01-15.txt",
      "date": "2024-01-15",
      "chunk_id": "meeting-2024-01-15.txt_chunk_0",
      "relevance_score": 0.87
    }
  ],
  "context_used": "[Source: meeting-2024-01-15.txt, Date: 2024-01-15, Chunk: 0]..."
}
```

### 2. Ingest New Transcripts

**Add files:**
```powershell
# Place your .txt files in data/transcripts/
Copy-Item "C:\path\to\your\transcript.txt" data\transcripts\
```

**Trigger ingestion:**
```powershell
curl -X POST "http://localhost:8000/ingest"
```

**Response:**
```json
{
  "message": "Ingestion complete. Added 5 new document chunks.",
  "new_documents_added": 5,
  "total_documents": 13
}
```

### 3. Check Status

```powershell
curl http://localhost:8000/status
```

### 4. List MCP Tools

```powershell
curl http://localhost:8000/tools
```

---

## Python Client

### Using the Test Client

```python
from test_client import ContextIQClient

# Initialize client
client = ContextIQClient("http://localhost:8000")

# Check status
status = client.status()
print(f"Total documents: {status['total_documents']}")

# Ask a question
result = client.ask("What are the action items?")
print(result['answer'])

# Show sources
for source in result['sources']:
    print(f"- {source['filename']} ({source['date']})")
```

### Direct API Usage

```python
import requests

# Ask a question
response = requests.post(
    "http://localhost:8000/ask",
    json={
        "question": "What database are we using?",
        "n_results": 5,
        "include_sources": True
    }
)

data = response.json()
print(data['answer'])
```

### Batch Questions

```python
from test_client import ContextIQClient

client = ContextIQClient()

questions = [
    "What is the MVP deadline?",
    "Who is responsible for the database schema?",
    "What time are the daily standups?",
    "What UI framework are we using?"
]

for question in questions:
    result = client.ask(question, n_results=3)
    print(f"\nQ: {question}")
    print(f"A: {result['answer']}\n")
```

---

## MCP Integration

### Connect from LM Studio

1. **Configure MCP Server**:
   - In LM Studio, go to Settings → MCP
   - Add new server: `http://localhost:8000`
   - Import tools from: `http://localhost:8000/tools`

2. **Available Tools**:
   - `search_transcripts` - Retrieves relevant context
   - `ask_about_transcripts` - Gets AI-generated answers

3. **Usage in Chat**:
   ```
   User: @search_transcripts What was discussed about the timeline?
   
   Assistant: [Uses MCP to search] Based on the transcripts, 
   the MVP deadline is March 1st...
   ```

### Direct MCP Tool Calls

```powershell
# Search transcripts
curl -X POST "http://localhost:8000/tools/search_transcripts" `
  -H "Content-Type: application/json" `
  -d '{"query": "action items", "n_results": 3}'

# Ask about transcripts
curl -X POST "http://localhost:8000/tools/ask_about_transcripts" `
  -H "Content-Type: application/json" `
  -d '{"question": "What are the deliverables?"}'
```

---

## Configuration

### Environment Variables (.env)

```env
# LM Studio Configuration
LM_STUDIO_BASE_URL=http://localhost:1234/v1
LM_STUDIO_API_KEY=lm-studio
LM_STUDIO_MODEL=local-model

# LLM Settings
LLM_TEMPERATURE=0.7           # Lower = more focused (0.0-1.0)
LLM_MAX_TOKENS=2048           # Maximum response length

# Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
SERVER_RELOAD=True            # Auto-reload on code changes

# Data Paths
TRANSCRIPTS_DIR=data/transcripts
DB_DIR=mcp/db
CHROMA_DIR=mcp/db/chroma

# RAG Settings
COLLECTION_NAME=transcripts
EMBEDDING_MODEL=all-MiniLM-L6-v2
DEFAULT_N_RESULTS=5           # Context chunks per query

# Chunking Settings
CHUNK_SIZE=500                # Words per chunk
CHUNK_OVERLAP=50              # Overlap between chunks
```

### Tuning for Your Data

**Large transcripts (>5000 words):**
```env
CHUNK_SIZE=1000
CHUNK_OVERLAP=100
DEFAULT_N_RESULTS=3
```

**Short messages (chat logs):**
```env
CHUNK_SIZE=200
CHUNK_OVERLAP=20
DEFAULT_N_RESULTS=10
```

**Better answer quality:**
```env
LLM_TEMPERATURE=0.3          # More focused
DEFAULT_N_RESULTS=8          # More context
```

---

## Examples

### Example 1: Team Standup Q&A

```python
from test_client import ContextIQClient

client = ContextIQClient()

# Ask about team updates
result = client.ask("What did Bob work on yesterday?")
print(result['answer'])
# Output: "Bob worked on the initial wireframes for the dashboard..."

# Ask about blockers
result = client.ask("Are there any blockers mentioned?")
print(result['answer'])
# Output: "No blockers were mentioned. Charlie and Bob both reported..."
```

### Example 2: Project Tracking

```python
# Find action items
result = client.ask("List all action items and who they're assigned to")

# Find deadlines
result = client.ask("What are the upcoming deadlines?")

# Track decisions
result = client.ask("What technical decisions were made?")
```

### Example 3: Adding New Data

```powershell
# Add a new transcript
echo "Meeting notes from today..." > data\transcripts\meeting-2024-11-05.txt

# Ingest it
curl -X POST http://localhost:8000/ingest

# Query it
$body = '{"question": "What happened in todays meeting?"}' 
curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d $body
```

### Example 4: Batch Processing

```python
import os
from pathlib import Path
from test_client import ContextIQClient

# Add multiple transcripts
transcript_dir = Path("data/transcripts")

for file in Path("C:/my_transcripts").glob("*.txt"):
    # Copy to transcripts directory
    dest = transcript_dir / file.name
    dest.write_text(file.read_text())

# Ingest all new files
client = ContextIQClient()
result = client.ingest()
print(f"Added {result['new_documents_added']} chunks from new transcripts")
```

---

## Troubleshooting

### Common Issues

**1. "Connection refused" to LM Studio**
```powershell
# Check if LM Studio is running
curl http://localhost:1234/v1/models

# If fails, start LM Studio and enable local server
```

**2. "No documents found"**
```powershell
# Check transcripts directory
ls data\transcripts\*.txt

# Manually trigger ingestion
curl -X POST http://localhost:8000/ingest
```

**3. Poor answer quality**
```env
# Increase context in .env
DEFAULT_N_RESULTS=10
CHUNK_SIZE=1000

# Restart server
```

**4. Server won't start**
```powershell
# Check if port is in use
netstat -ano | findstr :8000

# Use different port in .env
SERVER_PORT=8001
```

---

## Next Steps

1. **Add Your Data**: Place your transcript files in `data/transcripts/`
2. **Customize Prompts**: Edit system prompts in `mcp/llm.py`
3. **Tune Performance**: Adjust chunk size and overlap in `.env`
4. **Build Integration**: Use the Python client in your application
5. **Create UI**: Build a web interface using the API

---

## Additional Resources

- **API Documentation**: http://localhost:8000/docs (when server is running)
- **Project README**: See `README.md` for architecture details
- **Setup Guide**: See `SETUP.md` for installation help
- **Project Summary**: See `PROJECT_SUMMARY.md` for overview

---

**Built with ❤️ for local AI-powered knowledge management**
