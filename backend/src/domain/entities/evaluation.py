from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class EvaluationMetric(str, Enum):
    FAITHFULNESS = "FAITHFULNESS"
    ANSWER_RELEVANCE = "ANSWER_RELEVANCE"
    CONTEXT_RECALL = "CONTEXT_RECALL"
    GROUNDEDNESS = "GROUNDEDNESS"
    CITATION_ACCURACY = "CITATION_ACCURACY"

class EvaluationResult(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    conversation_id: UUID
    message_id: UUID
    metrics: Dict[str, float] = Field(default_factory=dict)
    hallucination_detected: bool = False
    hallucination_confidence: float = 0.0
    latency_ms: int = 0
    tokens_used: int = 0
    cost_usd: float = 0.0
    model_used: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RAGEvaluation(BaseModel):
    query: str
    answer: str
    contexts: List[str]
    ground_truth: Optional[str] = None
    faithfulness_score: Optional[float] = None
    answer_relevance_score: Optional[float] = None
    context_recall_score: Optional[float] = None
    groundedness_score: Optional[float] = None
    citation_accuracy_score: Optional[float] = None
