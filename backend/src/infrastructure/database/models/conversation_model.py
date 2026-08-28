from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Numeric, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from src.infrastructure.database.connection import Base


class ConversationModel(Base):
    __tablename__ = "conversations"
    __table_args__ = (
        Index("ix_conversations_workspace_id", "workspace_id"),
        Index("ix_conversations_user_id", "user_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(255), nullable=False)
    title = Column(String(500), nullable=True)
    total_tokens = Column(Integer, nullable=False, default=0)
    total_cost = Column(Numeric(10, 6), nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    messages = relationship("MessageModel", back_populates="conversation", cascade="all, delete-orphan", order_by="MessageModel.created_at")
    workspace = relationship("WorkspaceModel", back_populates="conversations")
    evaluation_results = relationship("EvaluationResultModel", back_populates="conversation", cascade="all, delete-orphan")


class MessageModel(Base):
    __tablename__ = "messages"
    __table_args__ = (
        Index("ix_messages_conversation_id", "conversation_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), nullable=False)  # USER | ASSISTANT | SYSTEM
    content = Column(Text, nullable=False)
    sources = Column(JSONB, nullable=False, default=list)  # List of Citation dicts
    token_count = Column(Integer, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    model_used = Column(String(100), nullable=True)
    cost_usd = Column(Numeric(10, 8), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    conversation = relationship("ConversationModel", back_populates="messages")
    evaluation_result = relationship("EvaluationResultModel", back_populates="message", uselist=False)
