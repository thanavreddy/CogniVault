from fastapi import APIRouter, Depends, HTTPException
from typing import List
from uuid import UUID

from src.application.dto.conversation_dto import SendMessageRequest, MessageResponse, ConversationResponse, ConversationListResponse
from src.application.use_cases.conversation_use_cases import CreateConversationUseCase, SendMessageUseCase, GetConversationHistoryUseCase
from src.api.dependencies import get_conversation_repository
from src.domain.repositories.conversation_repository import ConversationRepository

router = APIRouter(prefix="/conversations", tags=["conversations"])

@router.post("", response_model=ConversationResponse)
async def create_conversation(
    workspace_id: UUID,
    title: str,
    repo: ConversationRepository = Depends(get_conversation_repository)
):
    use_case = CreateConversationUseCase(repo)
    # mock user ID for now
    conv = await use_case.execute(workspace_id, UUID('00000000-0000-0000-0000-000000000000'), title)
    return ConversationResponse(
        id=conv.id,
        workspace_id=conv.workspace_id,
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at
    )

@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(
    conversation_id: UUID,
    request: SendMessageRequest,
    repo: ConversationRepository = Depends(get_conversation_repository)
):
    # Needs DocumentService for full RAG flow, returning 501 for scaffolding
    raise HTTPException(status_code=501, detail="Requires DocumentService injection")

@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: UUID,
    repo: ConversationRepository = Depends(get_conversation_repository)
):
    use_case = GetConversationHistoryUseCase(repo)
    messages = await use_case.execute(conversation_id)
    return [
        MessageResponse(
            id=m.id,
            conversation_id=m.conversation_id,
            role=m.role,
            content=m.content,
            sources=[], # Mapping needed
            latency_ms=m.latency_ms,
            model_used=m.model_used,
            token_count=m.token_count,
            cost_usd=m.cost_usd,
            created_at=m.created_at
        ) for m in messages
    ]
