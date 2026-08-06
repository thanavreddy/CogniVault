from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Enum as SQLEnum, Table
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone

from src.infrastructure.database.connection import Base
from src.domain.entities.workspace import WorkspacePlan, WorkspaceMemberRole

class WorkspaceModel(Base):
    __tablename__ = 'workspaces'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True, index=True)
    owner_id = Column(UUID(as_uuid=True), nullable=False)
    plan = Column(SQLEnum(WorkspacePlan), default=WorkspacePlan.FREE)
    settings = Column(JSONB, default=dict)
    document_count = Column(Integer, default=0)
    total_tokens_used = Column(Integer, default=0)
    monthly_cost_usd = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    members = relationship("WorkspaceMemberModel", back_populates="workspace", cascade="all, delete-orphan")


class WorkspaceMemberModel(Base):
    __tablename__ = 'workspace_members'

    workspace_id = Column(UUID(as_uuid=True), ForeignKey('workspaces.id', ondelete='CASCADE'), primary_key=True)
    user_id = Column(UUID(as_uuid=True), primary_key=True)
    role = Column(SQLEnum(WorkspaceMemberRole), nullable=False, default=WorkspaceMemberRole.MEMBER)
    joined_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    workspace = relationship("WorkspaceModel", back_populates="members")
