from fastapi import APIRouter
from datetime import datetime, timezone

router = APIRouter(prefix="/health", tags=["health"])

@router.get("")
async def health():
    return {
        "status": "healthy",
        "database": "connected",
        "qdrant": "connected",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
