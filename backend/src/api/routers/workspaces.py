"""Workspace management API endpoints."""
from uuid import UUID, uuid4
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import re

from src.api.dependencies import CurrentUser, WorkspaceRepo
from src.domain.entities.workspace import Workspace, WorkspacePlan

router = APIRouter()


class CreateWorkspaceRequest(BaseModel):
    name: str
    plan: WorkspacePlan = WorkspacePlan.FREE


class UpdateWorkspaceRequest(BaseModel):
    name: Optional[str] = None
    settings: Optional[dict] = None


class AddMemberRequest(BaseModel):
    user_id: str
    role: str = "MEMBER"


def _slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_-]+', '-', slug)
    return slug[:63]  # Max slug length


@router.get("/me")
async def get_my_workspaces(
    user: CurrentUser,
    repo: WorkspaceRepo,
):
    """Get all workspaces the current user belongs to."""
    workspaces = await repo.get_by_member(user.user_id)
    return {"workspaces": [w.model_dump() for w in workspaces], "total": len(workspaces)}


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_workspace(
    request: CreateWorkspaceRequest,
    user: CurrentUser,
    repo: WorkspaceRepo,
):
    """Create a new workspace."""
    base_slug = _slugify(request.name)
    slug = base_slug
    
    # Ensure unique slug
    counter = 1
    while await repo.get_by_slug(slug):
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    workspace = Workspace(
        id=uuid4(),
        name=request.name,
        slug=slug,
        owner_id=user.user_id,
        plan=request.plan,
    )
    created = await repo.create(workspace)
    return created.model_dump()


@router.get("/{workspace_id}")
async def get_workspace(
    workspace_id: UUID,
    user: CurrentUser,
    repo: WorkspaceRepo,
):
    workspace = await repo.get_by_id(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Check membership
    members = await repo.get_members(workspace_id)
    member_ids = [m.user_id for m in members]
    if user.user_id not in member_ids:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return workspace.model_dump()


@router.patch("/{workspace_id}")
async def update_workspace(
    workspace_id: UUID,
    request: UpdateWorkspaceRequest,
    user: CurrentUser,
    repo: WorkspaceRepo,
):
    workspace = await repo.get_by_id(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if workspace.owner_id != user.user_id:
        raise HTTPException(status_code=403, detail="Only workspace owner can update")
    
    if request.name:
        workspace.name = request.name
    if request.settings:
        workspace.settings.update(request.settings)
    
    updated = await repo.update(workspace)
    return updated.model_dump()


@router.post("/{workspace_id}/members", status_code=status.HTTP_201_CREATED)
async def add_member(
    workspace_id: UUID,
    request: AddMemberRequest,
    user: CurrentUser,
    repo: WorkspaceRepo,
):
    workspace = await repo.get_by_id(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if workspace.owner_id != user.user_id:
        raise HTTPException(status_code=403, detail="Only owner can add members")
    
    member = await repo.add_member(workspace_id, request.user_id, request.role)
    return member.model_dump()


@router.delete("/{workspace_id}/members/{member_user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    workspace_id: UUID,
    member_user_id: str,
    user: CurrentUser,
    repo: WorkspaceRepo,
):
    workspace = await repo.get_by_id(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if workspace.owner_id != user.user_id:
        raise HTTPException(status_code=403, detail="Only owner can remove members")
    if member_user_id == workspace.owner_id:
        raise HTTPException(status_code=400, detail="Cannot remove workspace owner")
    
    removed = await repo.remove_member(workspace_id, member_user_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Member not found")


@router.get("/{workspace_id}/members")
async def list_members(
    workspace_id: UUID,
    user: CurrentUser,
    repo: WorkspaceRepo,
):
    workspace = await repo.get_by_id(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    members = await repo.get_members(workspace_id)
    return {"members": [m.model_dump() for m in members], "total": len(members)}
