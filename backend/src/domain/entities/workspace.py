from enum import Enum
from typing import Dict, Any, List
from uuid import UUID, uuid4
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class WorkspacePlan(str, Enum):
    FREE = "FREE"
    PROFESSIONAL = "PROFESSIONAL"
    ENTERPRISE = "ENTERPRISE"

class WorkspaceMemberRole(str, Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"
    VIEWER = "VIEWER"

class WorkspaceMember(BaseModel):
    workspace_id: UUID
    user_id: UUID
    role: WorkspaceMemberRole
    joined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Workspace(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    slug: str
    owner_id: UUID
    plan: WorkspacePlan = WorkspacePlan.FREE
    settings: Dict[str, Any] = Field(default_factory=dict)
    member_ids: List[UUID] = Field(default_factory=list)
    document_count: int = 0
    total_tokens_used: int = 0
    monthly_cost_usd: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
