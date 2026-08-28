"""Conversation and chat API endpoints."""
from uuid import UUID
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio
import json

from src.api.dependencies import (
    CurrentUser, ConversationRepo, VectorStore, EmbeddingService,
    get_ollama_client, get_model_router,
)
from src.application.use_cases.conversation_use_cases import (
    CreateConversationUseCase,
    SendMessageUseCase,
    GetConversationHistoryUseCase,
    DeleteConversationUseCase,
)
from src.application.rag.rag_pipeline import RAGPipeline
from src.infrastructure.llm.ollama_client import OllamaLLMClient
from src.infrastructure.llm.model_router import ModelRouter

router = APIRouter()


class SendMessageRequest(BaseModel):
    content: str
    workspace_id: UUID
    conversation_id: Optional[UUID] = None
    document_ids: Optional[List[UUID]] = None
    force_model: Optional[str] = None


class CreateConversationRequest(BaseModel):
    workspace_id: UUID
    title: Optional[str] = None


def _make_rag_pipeline(
    vector_store, embedding_service, ollama_client, model_router
) -> RAGPipeline:
    return RAGPipeline(
        vector_store=vector_store,
        embedding_service=embedding_service,
        ollama_client=ollama_client,
        model_router=model_router,
    )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_conversation(
    request: CreateConversationRequest,
    user: CurrentUser,
    conv_repo: ConversationRepo,
):
    use_case = CreateConversationUseCase(conv_repo)
    conversation = await use_case.execute(
        workspace_id=request.workspace_id,
        user_id=user.user_id,
        title=request.title,
    )
    return {
        "id": str(conversation.id),
        "title": conversation.title,
        "workspace_id": str(conversation.workspace_id),
        "created_at": conversation.created_at.isoformat(),
    }


@router.get("/")
async def list_conversations(
    workspace_id: UUID,
    user: CurrentUser,
    conv_repo: ConversationRepo,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    use_case = GetConversationHistoryUseCase(conv_repo)
    conversations = await use_case.execute(
        workspace_id=workspace_id,
        user_id=user.user_id,
        skip=skip,
        limit=limit,
    )
    return {
        "conversations": [
            {
                "id": str(c.id),
                "title": c.title,
                "total_tokens": c.total_tokens,
                "total_cost": c.total_cost,
                "message_count": len(c.messages),
                "created_at": c.created_at.isoformat(),
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            }
            for c in conversations
        ],
        "total": len(conversations),
    }


@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: UUID,
    user: CurrentUser,
    conv_repo: ConversationRepo,
):
    conversation = await conv_repo.get_by_id(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conversation.user_id != user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return {
        "id": str(conversation.id),
        "title": conversation.title,
        "workspace_id": str(conversation.workspace_id),
        "total_tokens": conversation.total_tokens,
        "total_cost": conversation.total_cost,
        "messages": [
            {
                "id": str(m.id),
                "role": m.role.value,
                "content": m.content,
                "sources": [
                    {
                        "document_id": str(s.document_id),
                        "document_title": s.document_title,
                        "content_snippet": s.content_snippet,
                        "page_number": s.page_number,
                        "relevance_score": s.relevance_score,
                    }
                    for s in m.sources
                ],
                "token_count": m.token_count,
                "latency_ms": m.latency_ms,
                "model_used": m.model_used,
                "cost_usd": m.cost_usd,
                "created_at": m.created_at.isoformat(),
            }
            for m in conversation.messages
        ],
        "created_at": conversation.created_at.isoformat(),
    }


@router.post("/{conversation_id}/messages")
async def send_message(
    conversation_id: UUID,
    request: SendMessageRequest,
    user: CurrentUser,
    conv_repo: ConversationRepo,
    vector_store: VectorStore,
    embedding_service: EmbeddingService,
    ollama_client: OllamaLLMClient = Depends(get_ollama_client),
    model_router: ModelRouter = Depends(get_model_router),
):
    """Send a message and get an AI response. The core RAG endpoint."""
    rag_pipeline = _make_rag_pipeline(
        vector_store, embedding_service, ollama_client, model_router
    )
    use_case = SendMessageUseCase(conv_repo, rag_pipeline)

    try:
        conversation, message = await use_case.execute(
            content=request.content,
            workspace_id=request.workspace_id,
            user_id=user.user_id,
            conversation_id=conversation_id,
            document_ids=request.document_ids,
            force_model=request.force_model,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

    return {
        "conversation_id": str(conversation.id),
        "message": {
            "id": str(message.id),
            "role": message.role.value,
            "content": message.content,
            "sources": [
                {
                    "document_id": str(s.document_id),
                    "document_title": s.document_title,
                    "content_snippet": s.content_snippet,
                    "page_number": s.page_number,
                    "relevance_score": s.relevance_score,
                }
                for s in message.sources
            ],
            "model_used": message.model_used,
            "token_count": message.token_count,
            "latency_ms": message.latency_ms,
            "cost_usd": message.cost_usd,
            "created_at": message.created_at.isoformat(),
        },
    }


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: UUID,
    user: CurrentUser,
    conv_repo: ConversationRepo,
):
    use_case = DeleteConversationUseCase(conv_repo)
    try:
        await use_case.execute(conversation_id, user.user_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Conversation not found")
    except PermissionError:
        raise HTTPException(status_code=403, detail="Access denied")


@router.get("/{conversation_id}/messages")
async def get_messages(
    conversation_id: UUID,
    user: CurrentUser,
    conv_repo: ConversationRepo,
):
    conversation = await conv_repo.get_by_id(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    messages = await conv_repo.get_messages(conversation_id)
    return {
        "conversation_id": str(conversation_id),
        "messages": [
            {
                "id": str(m.id),
                "role": m.role.value,
                "content": m.content,
                "model_used": m.model_used,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ],
        "total": len(messages),
    }
