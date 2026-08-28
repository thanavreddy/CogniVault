"""Analytics and usage reporting endpoints."""
from uuid import UUID
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text

from src.api.dependencies import CurrentUser
from src.infrastructure.database.connection import get_db
from src.infrastructure.database.models.document_model import DocumentModel
from src.infrastructure.database.models.conversation_model import ConversationModel, MessageModel
from src.infrastructure.database.models.evaluation_model import EvaluationResultModel

router = APIRouter()


@router.get("/overview")
async def get_analytics_overview(
    workspace_id: UUID,
    user: CurrentUser,
    session: AsyncSession = Depends(get_db),
):
    """High-level stats for a workspace dashboard."""
    # Document count
    doc_result = await session.execute(
        select(func.count(DocumentModel.id))
        .where(DocumentModel.workspace_id == workspace_id)
    )
    doc_count = doc_result.scalar_one() or 0
    
    # Conversation count
    conv_result = await session.execute(
        select(func.count(ConversationModel.id))
        .where(ConversationModel.workspace_id == workspace_id)
    )
    conv_count = conv_result.scalar_one() or 0
    
    # Total tokens + cost
    token_result = await session.execute(
        select(
            func.sum(ConversationModel.total_tokens).label("total_tokens"),
            func.sum(ConversationModel.total_cost).label("total_cost"),
        )
        .where(ConversationModel.workspace_id == workspace_id)
    )
    token_row = token_result.one()
    total_tokens = int(token_row.total_tokens or 0)
    total_cost = float(token_row.total_cost or 0.0)
    
    # Message count
    msg_result = await session.execute(
        select(func.count(MessageModel.id))
        .join(ConversationModel, MessageModel.conversation_id == ConversationModel.id)
        .where(ConversationModel.workspace_id == workspace_id)
    )
    msg_count = msg_result.scalar_one() or 0
    
    # Hallucination rate
    hal_result = await session.execute(
        select(
            func.count(EvaluationResultModel.id).label("total"),
            func.sum(
                func.cast(EvaluationResultModel.hallucination_detected, type_=func.Integer)
            ).label("hallucinations"),
        )
        .join(ConversationModel, EvaluationResultModel.conversation_id == ConversationModel.id)
        .where(ConversationModel.workspace_id == workspace_id)
    )
    hal_row = hal_result.one()
    total_evals = int(hal_row.total or 0)
    hallucinations = int(hal_row.hallucinations or 0)
    hallucination_rate = (hallucinations / total_evals) if total_evals > 0 else 0.0
    
    return {
        "workspace_id": str(workspace_id),
        "document_count": doc_count,
        "conversation_count": conv_count,
        "message_count": msg_count,
        "total_tokens_used": total_tokens,
        "total_cost_usd": round(total_cost, 6),
        "evaluation_count": total_evals,
        "hallucination_rate": round(hallucination_rate, 4),
        "as_of": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/usage")
async def get_daily_usage(
    workspace_id: UUID,
    user: CurrentUser,
    days: int = Query(default=30, ge=1, le=365),
    session: AsyncSession = Depends(get_db),
):
    """Daily token usage and cost for charting."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    
    result = await session.execute(
        select(
            func.date(MessageModel.created_at).label("date"),
            func.sum(MessageModel.token_count).label("tokens"),
            func.sum(MessageModel.cost_usd).label("cost"),
            func.count(MessageModel.id).label("messages"),
        )
        .join(ConversationModel, MessageModel.conversation_id == ConversationModel.id)
        .where(
            ConversationModel.workspace_id == workspace_id,
            MessageModel.created_at >= since,
        )
        .group_by(func.date(MessageModel.created_at))
        .order_by(func.date(MessageModel.created_at))
    )
    rows = result.all()
    return {
        "workspace_id": str(workspace_id),
        "period_days": days,
        "data": [
            {
                "date": str(row.date),
                "tokens": int(row.tokens or 0),
                "cost_usd": round(float(row.cost or 0.0), 6),
                "messages": int(row.messages or 0),
            }
            for row in rows
        ],
    }


@router.get("/models")
async def get_model_usage(
    workspace_id: UUID,
    user: CurrentUser,
    session: AsyncSession = Depends(get_db),
):
    """Token and cost usage broken down by model."""
    result = await session.execute(
        select(
            MessageModel.model_used.label("model"),
            func.count(MessageModel.id).label("requests"),
            func.sum(MessageModel.token_count).label("tokens"),
            func.sum(MessageModel.cost_usd).label("cost"),
            func.avg(MessageModel.latency_ms).label("avg_latency_ms"),
        )
        .join(ConversationModel, MessageModel.conversation_id == ConversationModel.id)
        .where(
            ConversationModel.workspace_id == workspace_id,
            MessageModel.model_used.isnot(None),
            MessageModel.role == "ASSISTANT",
        )
        .group_by(MessageModel.model_used)
        .order_by(func.sum(MessageModel.cost_usd).desc())
    )
    rows = result.all()
    return {
        "workspace_id": str(workspace_id),
        "models": [
            {
                "model": row.model,
                "requests": int(row.requests or 0),
                "tokens": int(row.tokens or 0),
                "cost_usd": round(float(row.cost or 0.0), 6),
                "avg_latency_ms": round(float(row.avg_latency_ms or 0.0), 1),
            }
            for row in rows
        ],
    }


@router.get("/evaluation")
async def get_evaluation_scores(
    workspace_id: UUID,
    user: CurrentUser,
    session: AsyncSession = Depends(get_db),
):
    """Average evaluation metric scores for the workspace."""
    result = await session.execute(
        select(
            func.avg(EvaluationResultModel.hallucination_confidence).label("avg_hallucination_confidence"),
            func.count(EvaluationResultModel.id).label("total"),
            func.sum(
                func.cast(EvaluationResultModel.hallucination_detected, type_=func.Integer)
            ).label("hallucination_count"),
        )
        .join(ConversationModel, EvaluationResultModel.conversation_id == ConversationModel.id)
        .where(ConversationModel.workspace_id == workspace_id)
    )
    row = result.one()
    total = int(row.total or 0)
    hallucination_count = int(row.hallucination_count or 0)
    
    return {
        "workspace_id": str(workspace_id),
        "total_evaluations": total,
        "hallucination_rate": round(hallucination_count / total, 4) if total > 0 else 0.0,
        "avg_hallucination_confidence": round(float(row.avg_hallucination_confidence or 0.0), 4),
        "hallucination_count": hallucination_count,
    }
