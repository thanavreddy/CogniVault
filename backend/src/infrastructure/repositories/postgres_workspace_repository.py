"""PostgreSQL implementation of WorkspaceRepository."""
from uuid import UUID
from typing import Optional
from datetime import datetime, timezone
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from src.domain.entities.workspace import Workspace, WorkspaceMember, WorkspacePlan
from src.domain.repositories.workspace_repository import WorkspaceRepository
from src.infrastructure.database.models.workspace_model import WorkspaceModel, WorkspaceMemberModel

logger = logging.getLogger(__name__)


class PostgresWorkspaceRepository(WorkspaceRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_entity(model: WorkspaceModel) -> Workspace:
        return Workspace(
            id=model.id,
            name=model.name,
            slug=model.slug,
            owner_id=model.owner_id,
            plan=WorkspacePlan(model.plan),
            settings=model.settings_ or {},
            document_count=model.document_count or 0,
            total_tokens_used=model.total_tokens_used or 0,
            monthly_cost_usd=float(model.monthly_cost_usd) if model.monthly_cost_usd else 0.0,
            created_at=model.created_at,
        )

    @staticmethod
    def _member_to_entity(model: WorkspaceMemberModel) -> WorkspaceMember:
        return WorkspaceMember(
            workspace_id=model.workspace_id,
            user_id=model.user_id,
            role=model.role,
            joined_at=model.joined_at,
        )

    async def get_by_id(self, workspace_id: UUID) -> Optional[Workspace]:
        result = await self._session.execute(
            select(WorkspaceModel).where(WorkspaceModel.id == workspace_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_slug(self, slug: str) -> Optional[Workspace]:
        result = await self._session.execute(
            select(WorkspaceModel).where(WorkspaceModel.slug == slug)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_owner(self, owner_id: str) -> list[Workspace]:
        result = await self._session.execute(
            select(WorkspaceModel).where(WorkspaceModel.owner_id == owner_id)
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def get_by_member(self, user_id: str) -> list[Workspace]:
        result = await self._session.execute(
            select(WorkspaceModel)
            .join(WorkspaceMemberModel, WorkspaceModel.id == WorkspaceMemberModel.workspace_id)
            .where(WorkspaceMemberModel.user_id == user_id)
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def create(self, workspace: Workspace) -> Workspace:
        model = WorkspaceModel(
            id=workspace.id,
            name=workspace.name,
            slug=workspace.slug,
            owner_id=workspace.owner_id,
            plan=workspace.plan.value,
            settings_=workspace.settings,
        )
        self._session.add(model)
        # Also add the owner as a member with OWNER role
        member = WorkspaceMemberModel(
            workspace_id=workspace.id,
            user_id=workspace.owner_id,
            role="OWNER",
        )
        self._session.add(member)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def update(self, workspace: Workspace) -> Workspace:
        await self._session.execute(
            update(WorkspaceModel)
            .where(WorkspaceModel.id == workspace.id)
            .values(
                name=workspace.name,
                plan=workspace.plan.value,
                settings_=workspace.settings,
                updated_at=datetime.now(timezone.utc),
            )
        )
        await self._session.flush()
        return await self.get_by_id(workspace.id)

    async def delete(self, workspace_id: UUID) -> bool:
        result = await self._session.execute(
            delete(WorkspaceModel).where(WorkspaceModel.id == workspace_id)
        )
        await self._session.flush()
        return result.rowcount > 0

    async def add_member(self, workspace_id: UUID, user_id: str, role: str = "MEMBER") -> WorkspaceMember:
        member = WorkspaceMemberModel(
            workspace_id=workspace_id,
            user_id=user_id,
            role=role,
        )
        self._session.add(member)
        await self._session.flush()
        await self._session.refresh(member)
        return self._member_to_entity(member)

    async def remove_member(self, workspace_id: UUID, user_id: str) -> bool:
        result = await self._session.execute(
            delete(WorkspaceMemberModel)
            .where(
                WorkspaceMemberModel.workspace_id == workspace_id,
                WorkspaceMemberModel.user_id == user_id,
            )
        )
        await self._session.flush()
        return result.rowcount > 0

    async def get_members(self, workspace_id: UUID) -> list[WorkspaceMember]:
        result = await self._session.execute(
            select(WorkspaceMemberModel)
            .where(WorkspaceMemberModel.workspace_id == workspace_id)
        )
        return [self._member_to_entity(m) for m in result.scalars().all()]

    async def increment_document_count(self, workspace_id: UUID, delta: int = 1) -> None:
        await self._session.execute(
            update(WorkspaceModel)
            .where(WorkspaceModel.id == workspace_id)
            .values(document_count=WorkspaceModel.document_count + delta)
        )
        await self._session.flush()
