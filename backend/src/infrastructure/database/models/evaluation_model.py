from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Numeric, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from src.infrastructure.database.connection import Base


class EvaluationResultModel(Base):
    __tablename__ = "evaluation_results"
    __table_args__ = (
        Index("ix_evaluation_results_conversation_id", "conversation_id"),
        Index("ix_evaluation_results_message_id", "message_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    metrics = Column(JSONB, nullable=False, default=dict)  # {faithfulness: 0.9, relevance: 0.8, ...}
    hallucination_detected = Column(Boolean, nullable=False, default=False)
    hallucination_confidence = Column(Float, nullable=False, default=0.0)
    latency_ms = Column(Integer, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    cost_usd = Column(Numeric(10, 8), nullable=True)
    model_used = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    conversation = relationship("ConversationModel", back_populates="evaluation_results")
    message = relationship("MessageModel", back_populates="evaluation_result")
