"""Health check endpoints."""
from datetime import datetime, timezone
from fastapi import APIRouter
from src.infrastructure.database.connection import health_check as db_health_check

router = APIRouter()


@router.get("/health", tags=["Health"])
async def health_check():
    """Check system health. Used by load balancers and Docker health checks."""
    db_status = await db_health_check()
    all_healthy = db_status["status"] == "healthy"
    return {
        "status": "healthy" if all_healthy else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "database": db_status,
        },
    }


@router.get("/health/ready", tags=["Health"])
async def readiness_check():
    """Kubernetes readiness probe."""
    return {"status": "ready"}


@router.get("/health/live", tags=["Health"])
async def liveness_check():
    """Kubernetes liveness probe."""
    return {"status": "alive"}
