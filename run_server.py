"""
Simple script to run the MCP server
Usage: python run_server.py
"""
import uvicorn
from mcp.config import settings

if __name__ == "__main__":
    print("=" * 60)
    print("Starting ContextIQ MCP Server")
    print("=" * 60)
    print(f"Server: http://{settings.server_host}:{settings.server_port}")
    print(f"Docs:   http://localhost:{settings.server_port}/docs")
    print(f"LM Studio: {settings.lm_studio_base_url}")
    print("=" * 60)
    print("\nPress Ctrl+C to stop the server\n")
    
    uvicorn.run(
        "mcp.server:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=settings.server_reload,
        log_level="info"
    )
