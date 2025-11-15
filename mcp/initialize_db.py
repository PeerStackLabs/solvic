import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from server import TranscriptRAGServer

def initialize():
    print("Initializing ChromaDB")
    rag = TranscriptRAGServer()
    rag.initialize_db()
    
    count = rag.collection.count()
    print(f"Database initialized with {count} chunks")
    
    if results['documents'][0]:
        print(results['documents'][0][0][:200] + "...")
    
    print("\ncan connect now.")

if __name__ == "__main__":
    initialize()
