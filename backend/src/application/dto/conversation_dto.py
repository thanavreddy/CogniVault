from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from src.domain.entities.conversation import MessageRole

class SendMessageRequest(BaseModel):
    query: str
    conversation_id: Optional[UUID] = None
    workspace_id: UUID
    filters: Optional[Dict[str, Any]] = None

class CitationDTO(BaseModel):
    document_id: UUID
    document_title: str
    chunk_id: UUID
    content_snippet: str
    page_number: Optional[int] = None
    relevance_score: float

class MessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    role: MessageRole
    content: str
    sources: List[CitationDTO] = []
    latency_ms: int = 0
    model_used: Optional[str] = None
    token_count: int = 0
    cost_usd: float = 0.0
    created_at: datetime

class ConversationResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    title: str
    created_at: datetime
    updated_at: datetime

class ConversationListResponse(BaseModel):
    items: List[ConversationResponse]
    total: int
