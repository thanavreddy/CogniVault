from fastapi import APIRouter

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/overview")
async def get_overview():
    return {
        "total_documents": 0,
        "total_conversations": 0,
        "total_tokens": 0,
        "total_cost": 0.0
    }

@router.get("/usage")
async def get_usage():
    return []

@router.get("/models")
async def get_models():
    return []
