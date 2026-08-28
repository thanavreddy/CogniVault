"""RAG Pipeline — orchestrates the full retrieval-augmented generation flow.

Flow:
  1. Route query to optimal model
  2. Retrieve relevant chunks from Qdrant
  3. Build optimized context window
  4. Generate grounded answer
  5. Generate citations
  6. Return structured response
"""
import logging
import time
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from src.application.rag.context_builder import ContextBuilder
from src.application.rag.retriever import Retriever
from src.application.rag.citation_generator import CitationGenerator
from src.infrastructure.llm.model_router import ModelRouter
from src.infrastructure.llm.ollama_client import OllamaLLMClient
from src.infrastructure.vector_store.qdrant_client import QdrantVectorStore
from src.infrastructure.embeddings.ollama_embeddings import OllamaEmbeddingService
from src.domain.entities.conversation import Message, Citation
from src.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class RAGResponse:
    """The complete output of a RAG pipeline execution."""
    answer: str
    citations: list[Citation]
    model_used: str
    query_complexity: str
    token_count: int
    cost_usd: float
    latency_ms: float
    context_tokens: int
    chunks_retrieved: int
    chunks_used: int
    retrieved_chunks_scores: list[float]  # For evaluation


class RAGPipeline:
    """Orchestrates the full RAG pipeline."""

    def __init__(
        self,
        vector_store: QdrantVectorStore,
        embedding_service: OllamaEmbeddingService,
        ollama_client: OllamaLLMClient,
        model_router: ModelRouter,
        max_context_tokens: int = 8000,
    ) -> None:
        self._retriever = Retriever(vector_store, embedding_service)
        self._context_builder = ContextBuilder(max_tokens=max_context_tokens)
        self._citation_generator = CitationGenerator()
        self._ollama_client = ollama_client
        self._model_router = model_router

    async def run(
        self,
        query: str,
        workspace_id: str,
        conversation_history: list[Message] | None = None,
        document_ids: Optional[list[str]] = None,
        force_model: Optional[str] = None,
        top_k: int | None = None,
    ) -> RAGResponse:
        """Execute the full RAG pipeline for a user query."""
        start_time = time.time()
        top_k = top_k or settings.retrieval_top_k

        logger.info("RAG pipeline started: query='%s...' workspace=%s", query[:60], workspace_id)

        # ── Step 1: Retrieve relevant chunks ─────────────────────────────────
        retrieved_chunks = await self._retriever.retrieve(
            query=query,
            workspace_id=workspace_id,
            top_k=top_k,
            document_ids=document_ids,
        )
        logger.info("Retrieved %d chunks", len(retrieved_chunks))

        # ── Step 2: Route to optimal model ───────────────────────────────────
        routing = self._model_router.route(
            query=query,
            context_length=sum(len(c.content) for c in retrieved_chunks),
            has_retrieved_chunks=len(retrieved_chunks) > 0,
            force_model=force_model,
        )
        logger.info("Model routing: %s → %s", routing.complexity.value, routing.model)

        # ── Step 3: Build context ─────────────────────────────────────────────
        context_package = self._context_builder.build(
            query=query,
            retrieved_chunks=retrieved_chunks,
            conversation_history=conversation_history,
        )

        # ── Step 4: Generate answer ───────────────────────────────────────────
        llm_response = await self._ollama_client.complete(
            messages=context_package.messages,
            system_prompt=context_package.system_prompt,
            model=routing.model,
            max_tokens=1500,
        )
        token_count = llm_response.usage.get("total_tokens", 0)
        cost_usd = llm_response.cost
        latency_ms = llm_response.latency_ms

        answer = llm_response.content
        logger.info("Generated answer: %d chars, %d tokens, $%.6f", len(answer), token_count, cost_usd)

        # ── Step 5: Generate citations ────────────────────────────────────────
        citations = self._citation_generator.generate(
            retrieved_chunks=context_package.retrieved_chunks,
            answer=answer,
        )

        total_latency = (time.time() - start_time) * 1000

        return RAGResponse(
            answer=answer,
            citations=citations,
            model_used=routing.model,
            query_complexity=routing.complexity.value,
            token_count=token_count,
            cost_usd=cost_usd,
            latency_ms=total_latency,
            context_tokens=context_package.context_tokens,
            chunks_retrieved=len(retrieved_chunks),
            chunks_used=context_package.chunks_used,
            retrieved_chunks_scores=[c.score for c in retrieved_chunks],
        )
