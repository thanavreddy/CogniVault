"""Citation generator — creates structured source citations from retrieved chunks."""
import re
import logging
from uuid import UUID

from src.domain.entities.conversation import Citation
from src.infrastructure.vector_store.qdrant_client import SearchResult

logger = logging.getLogger(__name__)


class CitationGenerator:
    """Generates structured citations from retrieved chunks and LLM answer."""

    def generate(
        self,
        retrieved_chunks: list[SearchResult],
        answer: str,
        max_snippet_length: int = 250,
    ) -> list[Citation]:
        """Generate citations for chunks that were actually referenced in the answer."""
        citations = []
        
        for i, chunk in enumerate(retrieved_chunks):
            # Check if this source was referenced in the answer
            source_label = f"Source {i + 1}"
            is_cited = source_label in answer or self._is_content_referenced(chunk.content, answer)
            
            if is_cited or len(retrieved_chunks) <= 3:
                # For few results, include all; for many, only cited ones
                snippet = self._extract_snippet(chunk.content, max_snippet_length)
                
                try:
                    doc_id = UUID(chunk.document_id)
                    chunk_id = UUID(chunk.chunk_id)
                except (ValueError, AttributeError):
                    doc_id = UUID(int=0)
                    chunk_id = UUID(int=0)
                
                citations.append(Citation(
                    document_id=doc_id,
                    document_title=chunk.document_title or "Unknown Document",
                    chunk_id=chunk_id,
                    content_snippet=snippet,
                    page_number=chunk.page_number,
                    relevance_score=round(chunk.score, 4),
                ))
        
        # Sort by relevance score
        citations.sort(key=lambda c: c.relevance_score, reverse=True)
        
        logger.debug("Generated %d citations from %d chunks", len(citations), len(retrieved_chunks))
        return citations

    @staticmethod
    def _is_content_referenced(chunk_content: str, answer: str) -> bool:
        """Check if key phrases from the chunk appear in the answer."""
        # Extract key phrases (4+ word sequences) from chunk
        words = chunk_content.split()
        for i in range(len(words) - 3):
            phrase = " ".join(words[i : i + 4]).lower()
            if phrase in answer.lower():
                return True
        return False

    @staticmethod
    def _extract_snippet(content: str, max_length: int) -> str:
        """Extract the most informative snippet from a chunk."""
        if len(content) <= max_length:
            return content
        
        # Try to break at a sentence boundary
        truncated = content[:max_length]
        last_period = truncated.rfind(".")
        if last_period > max_length * 0.7:  # Don't truncate too aggressively
            return truncated[:last_period + 1]
        
        return truncated.rstrip() + "..."
