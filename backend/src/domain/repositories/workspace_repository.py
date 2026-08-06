from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from src.domain.entities.workspace import Workspace, WorkspaceMember

class WorkspaceRepository(ABC):
    @abstractmethod
    async def get_by_id(self, workspace_id: UUID) -> Optional[Workspace]:
        pass

    @abstractmethod
    async def get_by_slug(self, slug: str) -> Optional[Workspace]:
        pass

    @abstractmethod
    async def get_by_owner(self, owner_id: UUID) -> List[Workspace]:
        pass

    @abstractmethod
    async def create(self, workspace: Workspace) -> Workspace:
        pass

    @abstractmethod
    async def update(self, workspace: Workspace) -> Workspace:
        pass

    @abstractmethod
    async def delete(self, workspace_id: UUID) -> bool:
        pass

    @abstractmethod
    async def add_member(self, member: WorkspaceMember) -> WorkspaceMember:
        pass

    @abstractmethod
    async def remove_member(self, workspace_id: UUID, user_id: UUID) -> bool:
        pass

    @abstractmethod
    async def get_members(self, workspace_id: UUID) -> List[WorkspaceMember]:
        pass
