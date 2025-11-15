"""
RAG System using ChromaDB
Handles embedding storage, similarity search, and retrieval
"""
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from typing import List, Dict, Optional
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGSystem:
    """ChromaDB-based Retrieval Augmented Generation system"""
    
    def __init__(self, 
                 persist_directory: str = "mcp/db/chroma",
                 collection_name: str = "transcripts",
                 embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize RAG system with ChromaDB
        
        Args:
            persist_directory: Directory to persist ChromaDB
            collection_name: Name of the collection
            embedding_model: Sentence transformer model name
        """
        self.persist_directory = Path(persist_directory)
        self.collection_name = collection_name
        
        # Create persist directory
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Initialize embedding function
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"}
        )
        
        logger.info(f"RAG System initialized with {self.collection.count()} existing documents")
    
    def add_documents(self, documents: List[Dict]) -> int:
        """
        Add documents to the collection
        
        Args:
            documents: List of document dictionaries with 'text' and 'metadata'
            
        Returns:
            Number of documents added
        """
        if not documents:
            logger.warning("No documents to add")
            return 0
        
        # Prepare data for ChromaDB
        texts = [doc["text"] for doc in documents]
        metadatas = [doc["metadata"] for doc in documents]
        ids = [doc["metadata"]["chunk_id"] for doc in documents]
        
        # Check for existing IDs and filter them out
        existing_ids = set()
        try:
            # Query in batches to avoid overwhelming the system
            batch_size = 100
            for i in range(0, len(ids), batch_size):
                batch_ids = ids[i:i + batch_size]
                results = self.collection.get(ids=batch_ids)
                if results and results['ids']:
                    existing_ids.update(results['ids'])
        except Exception as e:
            logger.warning(f"Error checking existing IDs: {e}")
        
        # Filter out documents with existing IDs
        new_documents = []
        new_texts = []
        new_metadatas = []
        new_ids = []
        
        for doc, text, metadata, doc_id in zip(documents, texts, metadatas, ids):
            if doc_id not in existing_ids:
                new_documents.append(doc)
                new_texts.append(text)
                new_metadatas.append(metadata)
                new_ids.append(doc_id)
        
        if not new_texts:
            logger.info("All documents already exist in the collection")
            return 0
        
        # Add to collection
        try:
            self.collection.add(
                documents=new_texts,
                metadatas=new_metadatas,
                ids=new_ids
            )
            logger.info(f"Added {len(new_texts)} new documents to collection")
            return len(new_texts)
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise
    
    def query(self, 
              query_text: str, 
              n_results: int = 5,
              filter_metadata: Optional[Dict] = None) -> Dict:
        """
        Query the collection for similar documents
        
        Args:
            query_text: Query string
            n_results: Number of results to return
            filter_metadata: Optional metadata filter
            
        Returns:
            Dictionary with documents, metadatas, and distances
        """
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=filter_metadata
            )
            
            # Format results
            formatted_results = {
                "documents": results["documents"][0] if results["documents"] else [],
                "metadatas": results["metadatas"][0] if results["metadatas"] else [],
                "distances": results["distances"][0] if results["distances"] else [],
                "ids": results["ids"][0] if results["ids"] else []
            }
            
            return formatted_results
        except Exception as e:
            logger.error(f"Error querying collection: {e}")
            raise
    
    def get_collection_stats(self) -> Dict:
        """Get statistics about the collection"""
        try:
            count = self.collection.count()
            return {
                "total_documents": count,
                "collection_name": self.collection_name,
                "persist_directory": str(self.persist_directory)
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {"error": str(e)}
    
    def delete_collection(self):
        """Delete the entire collection (use with caution)"""
        try:
            self.client.delete_collection(name=self.collection_name)
            logger.info(f"Deleted collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            raise
    
    def reset_collection(self):
        """Reset the collection (delete and recreate)"""
        try:
            self.delete_collection()
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Reset collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error resetting collection: {e}")
            raise
    
    def build_context_from_results(self, results: Dict, max_chunks: int = 5) -> str:
        """
        Build a context string from query results
        
        Args:
            results: Query results from self.query()
            max_chunks: Maximum number of chunks to include
            
        Returns:
            Formatted context string
        """
        if not results["documents"]:
            return "No relevant context found."
        
        context_parts = []
        for idx, (doc, metadata) in enumerate(zip(
            results["documents"][:max_chunks], 
            results["metadatas"][:max_chunks]
        )):
            filename = metadata.get("filename", "Unknown")
            date = metadata.get("date", "Unknown")
            chunk_index = metadata.get("chunk_index", idx)
            
            context_parts.append(
                f"[Source: {filename}, Date: {date}, Chunk: {chunk_index}]\n{doc}\n"
            )
        
        return "\n---\n".join(context_parts)


# Utility functions for standalone usage
def create_rag_system(persist_directory: str = "mcp/db/chroma") -> RAGSystem:
    """Create and return a RAG system instance"""
    return RAGSystem(persist_directory=persist_directory)


def search_transcripts(query: str, 
                       rag_system: Optional[RAGSystem] = None,
                       n_results: int = 5) -> Dict:
    """
    Search transcripts for relevant information
    
    Args:
        query: Search query
        rag_system: Optional RAGSystem instance (creates new if None)
        n_results: Number of results to return
        
    Returns:
        Query results
    """
    if rag_system is None:
        rag_system = create_rag_system()
    
    return rag_system.query(query, n_results=n_results)
