"""PostgreSQL implementation of EvaluationRepository."""
from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime

from src.domain.entities.evaluation import EvaluationResult
from src.infrastructure.database.models.evaluation_model import EvaluationResultModel


class PostgresEvaluationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, result: EvaluationResult) -> EvaluationResult:
        model = EvaluationResultModel(
            id=result.id,
            conversation_id=result.conversation_id,
            message_id=result.message_id,
            metrics=result.metrics,
            hallucination_detected=result.hallucination_detected,
            hallucination_confidence=result.hallucination_confidence,
            latency_ms=result.latency_ms,
            tokens_used=result.tokens_used,
            cost_usd=result.cost_usd,
            model_used=result.model_used,
        )
        self._session.add(model)
        await self._session.flush()
        return result

    async def get_by_conversation(
        self, conversation_id: UUID
    ) -> list[EvaluationResult]:
        result = await self._session.execute(
            select(EvaluationResultModel)
            .where(EvaluationResultModel.conversation_id == conversation_id)
            .order_by(EvaluationResultModel.created_at.desc())
        )
        models = result.scalars().all()
        return [
            EvaluationResult(
                id=m.id,
                conversation_id=m.conversation_id,
                message_id=m.message_id,
                metrics=m.metrics or {},
                hallucination_detected=m.hallucination_detected,
                hallucination_confidence=m.hallucination_confidence,
                latency_ms=m.latency_ms,
                tokens_used=m.tokens_used,
                cost_usd=float(m.cost_usd) if m.cost_usd else None,
                model_used=m.model_used,
                created_at=m.created_at,
            )
            for m in models
        ]

    async def get_average_scores_for_workspace(
        self, workspace_id: UUID, since: Optional[datetime] = None
    ) -> dict[str, float]:
        """Return average metric scores for all evaluations in a workspace."""
        # This is a simplified version - in production use jsonb_each for proper aggregation
        result = await self._session.execute(
            select(
                func.avg(EvaluationResultModel.hallucination_confidence).label("avg_hallucination"),
                func.count(EvaluationResultModel.id).label("total"),
                func.sum(
                    func.cast(EvaluationResultModel.hallucination_detected, type_=func.Integer)
                ).label("hallucination_count"),
            )
            .join(EvaluationResultModel.conversation)
            .where(
                EvaluationResultModel.conversation.has(workspace_id=workspace_id)
            )
        )
        row = result.one()
        return {
            "avg_hallucination_confidence": float(row.avg_hallucination or 0.0),
            "total_evaluations": int(row.total or 0),
            "hallucination_count": int(row.hallucination_count or 0),
        }
