"""Local Ollama embedding service for Qdrant indexing and retrieval."""
import logging

from langchain_ollama import OllamaEmbeddings

from src.core.config import settings

logger = logging.getLogger(__name__)


class OllamaEmbeddingService:
    """Generate embeddings with a model separate from the chat model."""

    MAX_BATCH_SIZE = 64

    def __init__(self) -> None:
        self.model = settings.ollama_embedding_model
        self.dimensions = settings.embedding_dimensions
        self._embeddings = OllamaEmbeddings(
            base_url=settings.ollama_base_url,
            model=self.model,
        )

    async def embed_text(self, text: str) -> list[float]:
        """Embed one text using Ollama."""
        try:
            return await self._embeddings.aembed_query(text.replace("\n", " ").strip())
        except Exception as exc:
            raise RuntimeError(
                f"Ollama embedding failed for model '{self.model}'. Ensure Ollama is running "
                f"and the model is installed (ollama serve && ollama pull {self.model})."
            ) from exc

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed texts in batches using Ollama."""
        if not texts:
            return []
        cleaned = [text.replace("\n", " ").strip() for text in texts]
        try:
            results: list[list[float]] = []
            for start in range(0, len(cleaned), self.MAX_BATCH_SIZE):
                results.extend(await self._embeddings.aembed_documents(cleaned[start : start + self.MAX_BATCH_SIZE]))
            return results
        except Exception as exc:
            raise RuntimeError(
                f"Ollama embedding failed for model '{self.model}'. Ensure Ollama is running "
                f"and the model is installed (ollama serve && ollama pull {self.model})."
            ) from exc
