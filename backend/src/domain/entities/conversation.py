from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class MessageRole(str, Enum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"
    SYSTEM = "SYSTEM"

class Citation(BaseModel):
    document_id: UUID
    document_title: str
    chunk_id: UUID
    content_snippet: str
    page_number: Optional[int] = None
    relevance_score: float

class Message(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    conversation_id: UUID
    role: MessageRole
    content: str
    sources: List[Citation] = Field(default_factory=list)
    token_count: int = 0
    latency_ms: int = 0
    model_used: Optional[str] = None
    cost_usd: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Conversation(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    workspace_id: UUID
    user_id: UUID
    title: str
    messages: List[Message] = Field(default_factory=list)
    total_tokens: int = 0
    total_cost: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
