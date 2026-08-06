from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
import os

from src.infrastructure.database.connection import get_db
from src.infrastructure.repositories.postgres_document_repository import PostgresDocumentRepository
from src.infrastructure.repositories.postgres_conversation_repository import PostgresConversationRepository
from src.infrastructure.vector_store.qdrant_client import QdrantVectorStore
from src.infrastructure.embeddings.openai_embeddings import OpenAIEmbeddingService
from src.infrastructure.llm.model_router import ModelRouter
from src.domain.repositories.document_repository import DocumentRepository
from src.domain.repositories.conversation_repository import ConversationRepository
# from src.api.middleware.auth import verify_clerk_token

# class CurrentUser:
#     user_id: UUID
#     workspace_id: UUID

# async def get_current_user(token: str = Depends(verify_clerk_token)) -> CurrentUser:
#     # In real app, extract IDs from token claims
#     pass

def get_document_repository(session: AsyncSession = Depends(get_db)) -> DocumentRepository:
    return PostgresDocumentRepository(session)

def get_conversation_repository(session: AsyncSession = Depends(get_db)) -> ConversationRepository:
    return PostgresConversationRepository(session)

# def get_workspace_repository(session: AsyncSession = Depends(get_db)) -> WorkspaceRepository:
#     return PostgresWorkspaceRepository(session)

def get_vector_store() -> QdrantVectorStore:
    return QdrantVectorStore()

def get_embedding_service() -> OpenAIEmbeddingService:
    return OpenAIEmbeddingService()

def get_model_router() -> ModelRouter:
    return ModelRouter()
