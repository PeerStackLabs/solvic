"""
Configuration Management
Loads settings from environment variables with defaults
"""
from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path


class Settings(BaseSettings):
    """Application settings"""
    
    # LM Studio Configuration
    lm_studio_base_url: str = "http://localhost:1234/v1"
    lm_studio_api_key: str = "lm-studio"
    lm_studio_model: str = "local-model"
    
    # LLM Settings
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2048
    
    # Server Configuration
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    server_reload: bool = True
    
    # Data Paths
    transcripts_dir: str = "data/transcripts"
    db_dir: str = "mcp/db"
    chroma_dir: str = "mcp/db/chroma"
    
    # RAG Settings
    collection_name: str = "transcripts"
    embedding_model: str = "all-MiniLM-L6-v2"
    default_n_results: int = 5
    
    # Chunking Settings
    chunk_size: int = 500
    chunk_overlap: int = 50
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings"""
    return settings
