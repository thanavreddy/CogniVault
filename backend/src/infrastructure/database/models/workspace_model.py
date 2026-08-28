from sqlalchemy import Column, String, Integer, BigInteger, DateTime, ForeignKey, Numeric, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from src.infrastructure.database.connection import Base


class WorkspaceModel(Base):
    __tablename__ = "workspaces"
    __table_args__ = (
        Index("ix_workspaces_owner_id", "owner_id"),
        Index("ix_workspaces_slug", "slug", unique=True),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True)
    owner_id = Column(String(255), nullable=False)
    plan = Column(String(50), nullable=False, default="FREE")
    settings_ = Column("settings", JSONB, nullable=False, default=dict)
    document_count = Column(Integer, nullable=False, default=0)
    total_tokens_used = Column(BigInteger, nullable=False, default=0)
    monthly_cost_usd = Column(Numeric(10, 6), nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    members = relationship("WorkspaceMemberModel", back_populates="workspace", cascade="all, delete-orphan")
    documents = relationship("DocumentModel", back_populates="workspace", cascade="all, delete-orphan")
    conversations = relationship("ConversationModel", back_populates="workspace", cascade="all, delete-orphan")


class WorkspaceMemberModel(Base):
    __tablename__ = "workspace_members"
    __table_args__ = (
        Index("ix_workspace_members_user_id", "user_id"),
    )

    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(String(255), primary_key=True)
    role = Column(String(50), nullable=False, default="MEMBER")
    joined_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    workspace = relationship("WorkspaceModel", back_populates="members")
