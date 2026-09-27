from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List
from functools import lru_cache

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # App
    app_name: str = "CogniVault"
    app_env: str = Field(default="development", alias="APP_ENV")
    cors_origins: str = Field(default="http://localhost:3000")
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",")]
    
    # Qdrant
    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    qdrant_collection: str = Field(default="cognivault", alias="QDRANT_COLLECTION")
    
    # Local Ollama provider
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="qwen2.5:7b", alias="OLLAMA_MODEL")
    # Local documents
    documents_dir: str = Field(default="./data/documents", alias="DOCUMENTS_DIR")
    max_upload_size_mb: int = Field(default=50, alias="MAX_UPLOAD_SIZE_MB")
    supported_file_types: str = Field(default="pdf,docx,txt,md", alias="SUPPORTED_FILE_TYPES")
    
    @property
    def supported_file_types_list(self) -> List[str]:
        return [t.strip().lower() for t in self.supported_file_types.split(",")]
    
    # FastEmbed
    embedding_model: str = Field(default="BAAI/bge-small-en-v1.5", alias="EMBEDDING_MODEL")
    
    # Chunking
    chunk_size: int = Field(default=1000, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, alias="CHUNK_OVERLAP")
    
    chunk_size: int = Field(default=1000, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, alias="CHUNK_OVERLAP")
    retrieval_top_k: int = Field(default=4, alias="RETRIEVAL_TOP_K")


@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
