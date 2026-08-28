"""Retriever — semantic search with result deduplication and reranking."""
import logging
from typing import Optional
from uuid import UUID

from src.infrastructure.vector_store.qdrant_client import QdrantVectorStore, SearchResult
from src.infrastructure.embeddings.ollama_embeddings import OllamaEmbeddingService

logger = logging.getLogger(__name__)


class Retriever:
    """Retrieves relevant document chunks for a query."""

    def __init__(
        self,
        vector_store: QdrantVectorStore,
        embedding_service: OllamaEmbeddingService,
    ) -> None:
        self._vector_store = vector_store
        self._embedding_service = embedding_service

    async def retrieve(
        self,
        query: str,
        workspace_id: str,
        top_k: int = 10,
        document_ids: Optional[list[str]] = None,
        score_threshold: float = 0.4,
    ) -> list[SearchResult]:
        """Retrieve the most relevant chunks for a query."""
        # 1. Embed the query
        query_embedding = await self._embedding_service.embed_text(query)
        
        # 2. Semantic search in Qdrant
        results = await self._vector_store.search(
            query_embedding=query_embedding,
            workspace_id=workspace_id,
            top_k=top_k * 2,  # Over-retrieve for dedup/reranking
            document_ids=document_ids,
            score_threshold=score_threshold,
        )
        
        # 3. Deduplicate similar chunks
        results = self._deduplicate(results)
        
        # 4. Rerank by score and diversity
        results = self._rerank(results, top_k)
        
        logger.info(
            "Retrieved %d chunks for query '%s...' in workspace %s",
            len(results), query[:50], workspace_id,
        )
        return results

    async def multi_query_retrieve(
        self,
        queries: list[str],
        workspace_id: str,
        top_k: int = 10,
    ) -> list[SearchResult]:
        """Retrieve using multiple query variants and merge results."""
        all_results: dict[str, SearchResult] = {}
        
        for q in queries:
            results = await self.retrieve(q, workspace_id, top_k=top_k // len(queries) + 3)
            for result in results:
                chunk_id = result.chunk_id
                # Keep the highest scoring occurrence
                if chunk_id not in all_results or result.score > all_results[chunk_id].score:
                    all_results[chunk_id] = result
        
        # Sort by score and return top_k
        merged = sorted(all_results.values(), key=lambda r: r.score, reverse=True)
        return merged[:top_k]

    @staticmethod
    def _deduplicate(results: list[SearchResult]) -> list[SearchResult]:
        """Remove near-duplicate chunks (same document, adjacent chunks)."""
        seen_docs: dict[str, set[int]] = {}  # doc_id → set of chunk_indices
        deduped = []
        
        for result in results:
            doc_id = result.document_id
            chunk_idx = result.chunk_index
            
            if doc_id not in seen_docs:
                seen_docs[doc_id] = set()
            
            # Skip if adjacent chunk from same doc already included
            adjacent = {chunk_idx - 1, chunk_idx, chunk_idx + 1}
            if seen_docs[doc_id] & adjacent:
                continue
            
            seen_docs[doc_id].add(chunk_idx)
            deduped.append(result)
        
        return deduped

    @staticmethod
    def _rerank(
        results: list[SearchResult],
        top_k: int,
    ) -> list[SearchResult]:
        """Rerank results balancing score and document diversity."""
        if not results:
            return []
        
        # MMR-inspired: penalize results from already-represented documents
        selected: list[SearchResult] = []
        remaining = list(results)
        doc_counts: dict[str, int] = {}
        
        while remaining and len(selected) < top_k:
            # Score = original_score * diversity_penalty
            scored = []
            for r in remaining:
                count = doc_counts.get(r.document_id, 0)
                diversity_penalty = 1.0 / (1.0 + count * 0.3)  # Penalize repeated docs
                adjusted_score = r.score * diversity_penalty
                scored.append((adjusted_score, r))
            
            # Pick highest adjusted score
            scored.sort(key=lambda x: x[0], reverse=True)
            best = scored[0][1]
            selected.append(best)
            remaining.remove(best)
            doc_counts[best.document_id] = doc_counts.get(best.document_id, 0) + 1
        
        return selected
