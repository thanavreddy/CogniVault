"""FastAPI dependency injection — wires together all repositories and services."""
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from src.infrastructure.database.connection import get_db
from src.infrastructure.repositories.postgres_document_repository import PostgresDocumentRepository
from src.infrastructure.repositories.postgres_conversation_repository import PostgresConversationRepository
from src.infrastructure.repositories.postgres_workspace_repository import PostgresWorkspaceRepository
from src.infrastructure.repositories.postgres_evaluation_repository import PostgresEvaluationRepository
from src.infrastructure.vector_store.qdrant_client import QdrantVectorStore
from src.infrastructure.embeddings.ollama_embeddings import OllamaEmbeddingService
from src.infrastructure.llm.model_router import ModelRouter
from src.infrastructure.llm.ollama_client import OllamaLLMClient
from src.api.middleware.auth import get_current_user, ClerkUser
from src.core.config import settings


# ── Singleton instances (created once per app lifetime) ──────────────────────
_qdrant_store = QdrantVectorStore()
_embedding_service = OllamaEmbeddingService()
_model_router = ModelRouter()
_ollama_client = OllamaLLMClient()


# ── Session-scoped (created per request) ─────────────────────────────────────
def get_document_repository(
    session: AsyncSession = Depends(get_db),
) -> PostgresDocumentRepository:
    return PostgresDocumentRepository(session)


def get_conversation_repository(
    session: AsyncSession = Depends(get_db),
) -> PostgresConversationRepository:
    return PostgresConversationRepository(session)


def get_workspace_repository(
    session: AsyncSession = Depends(get_db),
) -> PostgresWorkspaceRepository:
    return PostgresWorkspaceRepository(session)


def get_evaluation_repository(
    session: AsyncSession = Depends(get_db),
) -> PostgresEvaluationRepository:
    return PostgresEvaluationRepository(session)


# ── App-scoped singletons ─────────────────────────────────────────────────────
def get_vector_store() -> QdrantVectorStore:
    return _qdrant_store


def get_embedding_service() -> OllamaEmbeddingService:
    return _embedding_service


def get_model_router() -> ModelRouter:
    return _model_router


def get_ollama_client() -> OllamaLLMClient:
    return _ollama_client


# ── Type aliases for cleaner route signatures ─────────────────────────────────
CurrentUser = Annotated[ClerkUser, Depends(get_current_user)]
DocumentRepo = Annotated[PostgresDocumentRepository, Depends(get_document_repository)]
ConversationRepo = Annotated[PostgresConversationRepository, Depends(get_conversation_repository)]
WorkspaceRepo = Annotated[PostgresWorkspaceRepository, Depends(get_workspace_repository)]
EvaluationRepo = Annotated[PostgresEvaluationRepository, Depends(get_evaluation_repository)]
VectorStore = Annotated[QdrantVectorStore, Depends(get_vector_store)]
EmbeddingService = Annotated[OllamaEmbeddingService, Depends(get_embedding_service)]
