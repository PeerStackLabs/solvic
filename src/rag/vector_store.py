"""
Vector database manager for storing and retrieving meeting transcripts
"""
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from typing import List, Dict, Optional
import hashlib
import json
from datetime import datetime

class TranscriptVectorStore:
    def __init__(self, persist_directory: str = "./data/chroma_db"):
        """Initialize ChromaDB vector store"""
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Use sentence transformers for embeddings
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name="meeting_transcripts",
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"}
        )
    
    def _generate_id(self, transcript: Dict) -> str:
        """Generate unique ID for transcript"""
        content = f"{transcript['title']}_{transcript['timestamp']}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def add_transcript(self, transcript: Dict) -> bool:
        """
        Add a transcript to the vector store
        
        Args:
            transcript: Dict with 'title', 'content', 'timestamp', 'source'
        
        Returns:
            bool: True if added, False if duplicate
        """
        doc_id = self._generate_id(transcript)
        
        # Check if already exists
        try:
            existing = self.collection.get(ids=[doc_id])
            if existing['ids']:
                print(f"Transcript already indexed: {transcript['title']}")
                return False
        except:
            pass
        
        # Chunk the transcript for better retrieval
        chunks = self._chunk_transcript(transcript)
        
        ids = []
        documents = []
        metadatas = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_chunk_{i}"
            ids.append(chunk_id)
            documents.append(chunk)
            metadatas.append({
                "title": transcript['title'],
                "timestamp": transcript['timestamp'].isoformat() if isinstance(transcript['timestamp'], datetime) else str(transcript['timestamp']),
                "source": transcript.get('source', 'unknown'),
                "chunk_index": i,
                "parent_id": doc_id
            })
        
        # Add to collection
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        
        print(f"✅ Indexed transcript: {transcript['title']} ({len(chunks)} chunks)")
        return True
    
    def _chunk_transcript(self, transcript: Dict, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split transcript into overlapping chunks"""
        content = transcript['content']
        words = content.split()
        
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk:
                # Add context to each chunk
                header = f"Meeting: {transcript['title']}\nDate: {transcript['timestamp']}\n\n"
                chunks.append(header + chunk)
        
        return chunks if chunks else [content]
    
    def search(self, query: str, n_results: int = 5) -> List[Dict]:
        """
        Search for relevant transcript chunks
        
        Args:
            query: Search query
            n_results: Number of results to return
        
        Returns:
            List of relevant chunks with metadata
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                'content': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i]
            })
        
        return formatted_results
    
    def get_stats(self) -> Dict:
        """Get statistics about the vector store"""
        count = self.collection.count()
        
        # Get unique meetings
        all_docs = self.collection.get()
        unique_meetings = set()
        if all_docs['metadatas']:
            unique_meetings = set(m.get('parent_id', '') for m in all_docs['metadatas'])
        
        return {
            'total_chunks': count,
            'unique_meetings': len(unique_meetings),
            'collection_name': self.collection.name
        }
    
    def clear(self):
        """Clear all data from the vector store"""
        self.client.delete_collection("meeting_transcripts")
        self.collection = self.client.get_or_create_collection(
            name="meeting_transcripts",
            embedding_function=self.embedding_function
        )
        print("🗑️ Vector store cleared")
