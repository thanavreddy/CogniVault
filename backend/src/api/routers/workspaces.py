from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter(prefix="/workspaces", tags=["workspaces"])

@router.get("/me")
async def get_my_workspaces():
    return []

@router.post("")
async def create_workspace(name: str):
    return {"message": "Not implemented"}

@router.get("/{workspace_id}")
async def get_workspace(workspace_id: str):
    return {"id": workspace_id}
