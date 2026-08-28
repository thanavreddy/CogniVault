from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator
from typing import Optional, List
from functools import lru_cache

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # App
    app_name: str = "Enterprise AI Knowledge Assistant"
    app_env: str = Field(default="development", alias="APP_ENV")
    secret_key: str = Field(default="change-me-in-production", alias="SECRET_KEY")
    debug: bool = Field(default=False)
    cors_origins: str = Field(default="http://localhost:3000")
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",")]
    
    # Database
    database_url: str = Field(default="postgresql+asyncpg://postgres:postgres@localhost:5432/ai_assistant", alias="DATABASE_URL")
    database_pool_size: int = Field(default=20, alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=10, alias="DATABASE_MAX_OVERFLOW")
    database_pool_timeout: int = Field(default=30, alias="DATABASE_POOL_TIMEOUT")
    database_pool_recycle: int = Field(default=1800, alias="DATABASE_POOL_RECYCLE")
    
    # Qdrant
    qdrant_host: str = Field(default="localhost", alias="QDRANT_HOST")
    qdrant_port: int = Field(default=6333, alias="QDRANT_PORT")
    qdrant_api_key: Optional[str] = Field(default=None, alias="QDRANT_API_KEY")
    qdrant_collection_name: str = Field(default="knowledge_base", alias="QDRANT_COLLECTION_NAME")
    
    # Local Ollama provider
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="qwen2.5:7b", alias="OLLAMA_MODEL")
    ollama_embedding_model: str = Field(default="nomic-embed-text", alias="OLLAMA_EMBEDDING_MODEL")
    ollama_max_tokens: int = Field(default=2000, alias="OLLAMA_MAX_TOKENS")
    
    # Clerk
    clerk_secret_key: str = Field(default="", alias="CLERK_SECRET_KEY")
    clerk_publishable_key: str = Field(default="", alias="CLERK_PUBLISHABLE_KEY")
    clerk_jwt_issuer: str = Field(default="", alias="CLERK_JWT_ISSUER")
    
    # AgentOps (preserved — feature-flagged, not initialized by default)
    agentops_api_key: Optional[str] = Field(default=None, alias="AGENTOPS_API_KEY")
    
    # OpenTelemetry (preserved — feature-flagged, not initialized by default)
    otel_exporter_otlp_endpoint: str = Field(default="http://localhost:14268/api/traces", alias="OTEL_EXPORTER_OTLP_ENDPOINT")
    otel_service_name: str = Field(default="enterprise-ai-backend", alias="OTEL_SERVICE_NAME")
    
    # File uploads
    upload_dir: str = Field(default="./uploads", alias="UPLOAD_DIR")
    max_upload_size_mb: int = Field(default=50, alias="MAX_UPLOAD_SIZE_MB")
    supported_file_types: str = Field(default="pdf,docx,txt,md", alias="SUPPORTED_FILE_TYPES")
    
    @property
    def supported_file_types_list(self) -> List[str]:
        return [t.strip().lower() for t in self.supported_file_types.split(",")]
    
    # Embeddings
    embedding_model: str = Field(default="nomic-embed-text", alias="EMBEDDING_MODEL")
    embedding_dimensions: int = Field(default=768, alias="EMBEDDING_DIMENSIONS")
    
    # Chunking
    chunk_size: int = Field(default=1000, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, alias="CHUNK_OVERLAP")
    
    # RAG
    max_context_tokens: int = Field(default=8000, alias="MAX_CONTEXT_TOKENS")
    retrieval_top_k: int = Field(default=10, alias="RETRIEVAL_TOP_K")
    rerank_top_k: int = Field(default=5, alias="RERANK_TOP_K")
    
    # Guardrails
    hallucination_threshold: float = Field(default=0.7, alias="HALLUCINATION_THRESHOLD")
    


@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
