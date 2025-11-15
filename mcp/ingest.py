"""
Transcript Ingestion Module
Handles reading, chunking, and tracking of transcript files
"""
import os
import hashlib
import json
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime
import re


class TranscriptIngestor:
    """Manages transcript file ingestion and chunking"""
    
    def __init__(self, transcripts_dir: str = "data/transcripts", 
                 metadata_file: str = "mcp/db/processed_files.json"):
        """
        Initialize the ingestor
        
        Args:
            transcripts_dir: Directory containing transcript files
            metadata_file: JSON file to track processed files
        """
        self.transcripts_dir = Path(transcripts_dir)
        self.metadata_file = Path(metadata_file)
        self.processed_files = self._load_metadata()
        
        # Create necessary directories
        self.transcripts_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _load_metadata(self) -> Dict[str, str]:
        """Load metadata of previously processed files"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_metadata(self):
        """Save metadata of processed files"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.processed_files, f, indent=2)
    
    def _calculate_file_hash(self, filepath: Path) -> str:
        """Calculate SHA256 hash of a file"""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _extract_date_from_filename(self, filename: str) -> str:
        """
        Extract date from filename if present
        Expected formats: YYYY-MM-DD, YYYYMMDD, or falls back to file modification time
        """
        # Try to extract date from filename
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
            r'(\d{4}\d{2}\d{2})',     # YYYYMMDD
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, filename)
            if match:
                date_str = match.group(1)
                if '-' not in date_str and len(date_str) == 8:
                    # Convert YYYYMMDD to YYYY-MM-DD
                    date_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
                return date_str
        
        # Fallback to current date
        return datetime.now().strftime("%Y-%m-%d")
    
    def chunk_text(self, text: str, chunk_size: int = 500, 
                   overlap: int = 50) -> List[str]:
        """
        Split text into overlapping chunks
        
        Args:
            text: Text to chunk
            chunk_size: Approximate number of words per chunk
            overlap: Number of words to overlap between chunks
            
        Returns:
            List of text chunks
        """
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk)
        
        return chunks
    
    def read_transcript(self, filepath: Path) -> str:
        """Read transcript file content"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    
    def get_new_transcripts(self) -> List[Tuple[Path, str]]:
        """
        Get list of new or modified transcript files
        
        Returns:
            List of tuples (filepath, file_hash)
        """
        new_transcripts = []
        
        if not self.transcripts_dir.exists():
            return new_transcripts
        
        for filepath in self.transcripts_dir.glob("*.txt"):
            file_hash = self._calculate_file_hash(filepath)
            filename = filepath.name
            
            # Check if file is new or modified
            if filename not in self.processed_files or \
               self.processed_files[filename] != file_hash:
                new_transcripts.append((filepath, file_hash))
        
        return new_transcripts
    
    def process_transcript(self, filepath: Path, file_hash: str) -> List[Dict]:
        """
        Process a single transcript file into chunks with metadata
        
        Args:
            filepath: Path to transcript file
            file_hash: Hash of the file content
            
        Returns:
            List of chunk dictionaries with metadata
        """
        # Read transcript
        content = self.read_transcript(filepath)
        
        # Extract metadata
        filename = filepath.name
        date = self._extract_date_from_filename(filename)
        
        # Chunk the text
        chunks = self.chunk_text(content)
        
        # Create chunk documents with metadata
        documents = []
        for idx, chunk in enumerate(chunks):
            doc = {
                "text": chunk,
                "metadata": {
                    "filename": filename,
                    "date": date,
                    "chunk_id": f"{filename}_chunk_{idx}",
                    "chunk_index": idx,
                    "total_chunks": len(chunks),
                    "file_hash": file_hash
                }
            }
            documents.append(doc)
        
        # Mark file as processed
        self.processed_files[filename] = file_hash
        self._save_metadata()
        
        return documents
    
    def ingest_all_new_transcripts(self) -> List[Dict]:
        """
        Ingest all new or modified transcripts
        
        Returns:
            List of all chunk documents from new transcripts
        """
        all_documents = []
        new_transcripts = self.get_new_transcripts()
        
        if not new_transcripts:
            print("No new transcripts to process")
            return all_documents
        
        print(f"Processing {len(new_transcripts)} new/modified transcript(s)")
        
        for filepath, file_hash in new_transcripts:
            print(f"Processing: {filepath.name}")
            documents = self.process_transcript(filepath, file_hash)
            all_documents.extend(documents)
            print(f"  Created {len(documents)} chunks")
        
        print(f"Total chunks created: {len(all_documents)}")
        return all_documents


# Utility function for standalone usage
def ingest_transcripts(transcripts_dir: str = "data/transcripts") -> List[Dict]:
    """
    Convenience function to ingest all new transcripts
    
    Args:
        transcripts_dir: Directory containing transcript files
        
    Returns:
        List of chunk documents
    """
    ingestor = TranscriptIngestor(transcripts_dir)
    return ingestor.ingest_all_new_transcripts()
