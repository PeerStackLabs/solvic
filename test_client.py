"""
Simple test client for the MCP server
Demonstrates how to interact with the API
"""
import requests
import json
from typing import Optional


class ContextIQClient:
    """Simple client for ContextIQ MCP server"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    def ask(self, question: str, n_results: int = 5, include_sources: bool = True) -> dict:
        """Ask a question about the transcripts"""
        response = requests.post(
            f"{self.base_url}/ask",
            json={
                "question": question,
                "n_results": n_results,
                "include_sources": include_sources
            }
        )
        response.raise_for_status()
        return response.json()
    
    def ingest(self) -> dict:
        """Trigger manual ingestion of transcripts"""
        response = requests.post(f"{self.base_url}/ingest")
        response.raise_for_status()
        return response.json()
    
    def status(self) -> dict:
        """Get system status"""
        response = requests.get(f"{self.base_url}/status")
        response.raise_for_status()
        return response.json()
    
    def health(self) -> dict:
        """Check server health"""
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()


def main():
    """Example usage"""
    print("=" * 60)
    print("ContextIQ Test Client")
    print("=" * 60)
    
    # Initialize client
    client = ContextIQClient()
    
    # Check health
    print("\n1. Checking server health...")
    try:
        health = client.health()
        print(f"   ✓ Server is {health['status']}")
    except Exception as e:
        print(f"   ✗ Server not reachable: {e}")
        print("   ℹ Make sure server is running: python run_server.py")
        return
    
    # Get status
    print("\n2. Getting system status...")
    try:
        status = client.status()
        print(f"   ✓ Status: {status['status']}")
        print(f"   ✓ Documents: {status['total_documents']}")
        print(f"   ✓ LM Studio: {'Connected' if status['lm_studio_connected'] else 'Not connected'}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Trigger ingestion
    print("\n3. Triggering ingestion...")
    try:
        ingest_result = client.ingest()
        print(f"   ✓ {ingest_result['message']}")
        print(f"   ✓ New documents: {ingest_result['new_documents_added']}")
        print(f"   ✓ Total documents: {ingest_result['total_documents']}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Ask questions
    questions = [
        "What is the MVP deadline?",
        "What database are we using?",
        "What are the action items for the team?",
        "Is the dashboard mobile-responsive?"
    ]
    
    print("\n4. Asking questions...")
    for i, question in enumerate(questions, 1):
        print(f"\n   Q{i}: {question}")
        try:
            result = client.ask(question, n_results=3, include_sources=True)
            
            # Print answer
            print(f"   A{i}: {result['answer'][:200]}...")
            
            # Print sources
            if result.get('sources'):
                print(f"   Sources:")
                for source in result['sources'][:2]:
                    print(f"      - {source['filename']} ({source['date']}) "
                          f"[relevance: {source['relevance_score']:.2f}]")
        except Exception as e:
            print(f"   ✗ Error: {e}")
    
    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
