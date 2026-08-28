"""Dynamic model router — selects optimal LLM based on query complexity."""
import re
import logging
from enum import Enum
from typing import NamedTuple

from src.core.config import settings

logger = logging.getLogger(__name__)

# Complex query signals (words/phrases that indicate need for deep reasoning)
COMPLEX_SIGNALS = [
    r"\banalyze\b", r"\bcompare\b", r"\bcontrast\b", r"\bcritique\b",
    r"\bevaluate\b", r"\bsynthesize\b", r"\bexplain why\b", r"\bhow does\b",
    r"\bimplications\b", r"\bstrategy\b", r"\barchitecture\b", r"\btrade.?off\b",
    r"\bpros and cons\b", r"\badvantages and disadvantages\b",
]

# Knowledge search signals (need RAG retrieval)
KNOWLEDGE_SIGNALS = [
    r"\bwhat is\b", r"\bwhat was\b", r"\bwho is\b", r"\bwhere is\b",
    r"\bhow much\b", r"\bhow many\b", r"\bwhen did\b", r"\baccording to\b",
    r"\bfind\b", r"\bsearch\b", r"\blookup\b", r"\bshow me\b",
]


class QueryComplexity(str, Enum):
    SIMPLE = "SIMPLE"                       # Short conversational queries
    KNOWLEDGE_SEARCH = "KNOWLEDGE_SEARCH"   # RAG-based factual queries
    COMPLEX_REASONING = "COMPLEX_REASONING" # Deep analysis and synthesis


class RoutingDecision(NamedTuple):
    model: str
    complexity: QueryComplexity
    reasoning: str


class ModelRouter:
    """Routes queries to the most cost-effective model."""

    def __init__(self) -> None:
        self.model_simple = settings.ollama_model
        self.model_knowledge = settings.ollama_model
        self.model_reasoning = settings.ollama_model

        # Pricing per 1K tokens
        self._pricing = {settings.ollama_model: {"input": 0.0, "output": 0.0}}

    def estimate_complexity(
        self,
        query: str,
        context_length: int = 0,
        has_retrieved_chunks: bool = False,
    ) -> QueryComplexity:
        """Classify query complexity using heuristics."""
        query_lower = query.lower().strip()
        word_count = len(query.split())

        # Very short queries with no context are simple
        if word_count <= 5 and not has_retrieved_chunks:
            return QueryComplexity.SIMPLE

        # Check for complex reasoning signals
        for pattern in COMPLEX_SIGNALS:
            if re.search(pattern, query_lower):
                return QueryComplexity.COMPLEX_REASONING

        # Long queries that require analysis are complex
        if word_count > 60:
            return QueryComplexity.COMPLEX_REASONING

        # If RAG context is large, use smarter model
        if context_length > 4000:
            return QueryComplexity.COMPLEX_REASONING

        # Knowledge search signals or moderate context
        if has_retrieved_chunks or context_length > 0:
            return QueryComplexity.KNOWLEDGE_SEARCH

        for pattern in KNOWLEDGE_SIGNALS:
            if re.search(pattern, query_lower):
                return QueryComplexity.KNOWLEDGE_SEARCH

        # Moderate length 
        if word_count > 15:
            return QueryComplexity.KNOWLEDGE_SEARCH

        return QueryComplexity.SIMPLE

    def route(
        self,
        query: str,
        context_length: int = 0,
        has_retrieved_chunks: bool = False,
        force_model: str | None = None,
    ) -> RoutingDecision:
        """Get full routing decision with model name and reasoning."""
        if force_model:
            return RoutingDecision(
                model=force_model,
                complexity=QueryComplexity.KNOWLEDGE_SEARCH,
                reasoning=f"Forced model: {force_model}",
            )

        complexity = self.estimate_complexity(query, context_length, has_retrieved_chunks)

        model_map = {
            QueryComplexity.SIMPLE: self.model_simple,
            QueryComplexity.KNOWLEDGE_SEARCH: self.model_knowledge,
            QueryComplexity.COMPLEX_REASONING: self.model_reasoning,
        }
        reasoning_map = {
            QueryComplexity.SIMPLE: "Short/conversational query → cost-optimized model",
            QueryComplexity.KNOWLEDGE_SEARCH: "Knowledge retrieval query → balanced model",
            QueryComplexity.COMPLEX_REASONING: "Complex analysis query → most capable model",
        }

        decision = RoutingDecision(
            model=model_map[complexity],
            complexity=complexity,
            reasoning=reasoning_map[complexity],
        )
        logger.info(
            "Model routing: '%s...' → %s (%s)",
            query[:50], decision.model, decision.complexity.value,
        )
        return decision

    def estimate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """Estimate cost in USD."""
        pricing = self._pricing.get(model, self._pricing[self.model_simple])
        return round(
            (input_tokens / 1000) * pricing["input"]
            + (output_tokens / 1000) * pricing["output"],
            8,
        )

    def get_all_models(self) -> dict:
        """Return all configured models."""
        return {
            "simple": self.model_simple,
            "knowledge_search": self.model_knowledge,
            "complex_reasoning": self.model_reasoning,
        }
