"""Unit tests for RAG pipeline components."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.application.rag.context_builder import ContextBuilder, ContextPackage
from src.application.rag.citation_generator import CitationGenerator
from src.application.rag.retriever import Retriever
from src.infrastructure.vector_store.qdrant_client import SearchResult
from src.infrastructure.llm.model_router import ModelRouter, QueryComplexity
from src.infrastructure.document_processor.chunker import DocumentChunker


# ── ModelRouter tests ────────────────────────────────────────────────────────
class TestModelRouter:
    def setup_method(self):
        self.router = ModelRouter()

    def test_simple_query_routes_to_mini(self):
        decision = self.router.route("Hi", context_length=0, has_retrieved_chunks=False)
        assert decision.complexity == QueryComplexity.SIMPLE

    def test_analyze_keyword_routes_to_reasoning(self):
        decision = self.router.route(
            "Analyze the financial performance and compare Q3 vs Q4 results",
            context_length=100,
        )
        assert decision.complexity == QueryComplexity.COMPLEX_REASONING

    def test_knowledge_search_routes_correctly(self):
        decision = self.router.route(
            "What was our revenue in 2024?",
            has_retrieved_chunks=True,
        )
        assert decision.complexity in (QueryComplexity.KNOWLEDGE_SEARCH, QueryComplexity.COMPLEX_REASONING)

    def test_cost_estimation(self):
        cost = self.router.estimate_cost("qwen2.5:7b", 1000, 500)
        assert cost == 0
        assert isinstance(cost, float)

    def test_force_model_override(self):
        decision = self.router.route("Hi", force_model="qwen2.5:7b")
        assert decision.model == "qwen2.5:7b"


# ── ContextBuilder tests ─────────────────────────────────────────────────────
class TestContextBuilder:
    def setup_method(self):
        self.builder = ContextBuilder(max_tokens=4000)

    def _make_chunk(self, content: str, score: float = 0.9) -> SearchResult:
        return SearchResult(
            chunk_id=str(uuid4()),
            document_id=str(uuid4()),
            workspace_id="ws-123",
            score=score,
            content=content,
            document_title="Test Document",
            page_number=1,
        )

    def test_build_with_no_chunks(self):
        package = self.builder.build(
            query="What is the revenue?",
            retrieved_chunks=[],
        )
        assert isinstance(package, ContextPackage)
        assert package.chunks_used == 0
        assert "No relevant documents" in package.messages[-1]["content"]

    def test_build_with_chunks(self):
        chunks = [
            self._make_chunk("Revenue was $12.4M in Q3 2024."),
            self._make_chunk("Operating expenses were $8.1M."),
        ]
        package = self.builder.build(
            query="What is the revenue?",
            retrieved_chunks=chunks,
        )
        assert package.chunks_used == 2
        assert "[Source 1" in package.messages[-1]["content"]
        assert "Revenue was $12.4M" in package.messages[-1]["content"]

    def test_token_budget_respected(self):
        # Create many large chunks
        chunks = [
            self._make_chunk("word " * 500)  # ~500 tokens each
            for _ in range(20)
        ]
        package = self.builder.build("query", chunks)
        assert package.total_tokens <= 4000 + 200  # Small tolerance
        assert package.chunks_used < 20  # Not all chunks fit

    def test_system_prompt_included(self):
        package = self.builder.build("query", [])
        assert len(package.system_prompt) > 100


# ── CitationGenerator tests ──────────────────────────────────────────────────
class TestCitationGenerator:
    def setup_method(self):
        self.generator = CitationGenerator()

    def _make_chunk(self, content: str, title: str = "Report") -> SearchResult:
        return SearchResult(
            chunk_id=str(uuid4()),
            document_id=str(uuid4()),
            workspace_id="ws-123",
            score=0.85,
            content=content,
            document_title=title,
            page_number=3,
        )

    def test_generates_citations_for_referenced_content(self):
        chunks = [self._make_chunk("Revenue was twelve point four million dollars in Q3.")]
        answer = "[Source 1] Revenue was twelve point four million dollars in Q3."
        citations = self.generator.generate(chunks, answer)
        assert len(citations) > 0

    def test_snippet_truncated_to_max_length(self):
        long_content = "word " * 300
        chunks = [self._make_chunk(long_content)]
        citations = self.generator.generate(chunks, "[Source 1] relevant answer")
        if citations:
            assert len(citations[0].content_snippet) <= 260

    def test_relevance_score_preserved(self):
        chunk = self._make_chunk("test content")
        chunk.score = 0.92
        citations = self.generator.generate([chunk], "[Source 1] answer")
        if citations:
            assert abs(citations[0].relevance_score - 0.92) < 0.01


# ── DocumentChunker tests ────────────────────────────────────────────────────
class TestDocumentChunker:
    def setup_method(self):
        self.chunker = DocumentChunker()
        self.document_id = uuid4()

    def test_empty_text_returns_no_chunks(self):
        chunks = self.chunker.chunk("", self.document_id)
        assert chunks == []

    def test_short_text_produces_one_chunk(self):
        text = "This is a short document with only a few sentences. It should fit in one chunk."
        chunks = self.chunker.chunk(text, self.document_id, chunk_size=1000)
        assert len(chunks) == 1
        assert chunks[0].document_id == self.document_id
        assert chunks[0].chunk_index == 0
        assert chunks[0].content == text

    def test_long_text_produces_multiple_chunks(self):
        # Generate ~5000 word text
        text = "This is a test sentence with meaningful content. " * 200
        chunks = self.chunker.chunk(text, self.document_id, chunk_size=200, chunk_overlap=50)
        assert len(chunks) > 1

    def test_chunks_have_unique_ids(self):
        text = "Paragraph one content here. " * 20 + "\n\n" + "Paragraph two content here. " * 20
        chunks = self.chunker.chunk(text, self.document_id, chunk_size=100, chunk_overlap=20)
        ids = [str(c.id) for c in chunks]
        assert len(ids) == len(set(ids))  # All unique

    def test_chunks_have_sequential_indices(self):
        text = "Content. " * 100
        chunks = self.chunker.chunk(text, self.document_id, chunk_size=100, chunk_overlap=20)
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i

    def test_token_count_populated(self):
        text = "The quick brown fox jumps over the lazy dog."
        chunks = self.chunker.chunk(text, self.document_id)
        for chunk in chunks:
            assert chunk.token_count > 0
