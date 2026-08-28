"""Celery tasks for asynchronous document processing."""
import asyncio
import logging
from uuid import UUID

from src.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def run_async(coro):
    """Run an async coroutine from a sync Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(
    name="src.workers.document_tasks.process_document",
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # Retry after 60 seconds
)
def process_document(self, document_id: str, workspace_id: str) -> dict:
    """
    Background task: Extract text → Chunk → Embed → Store in Qdrant.
    
    This is the heavy lifting that shouldn't block the API.
    """
    try:
        logger.info("[Task] Processing document %s", document_id)
        result = run_async(_process_document_async(document_id, workspace_id))
        logger.info("[Task] Document %s processed: %d chunks", document_id, result.get("total_chunks", 0))
        return result
    except Exception as exc:
        logger.error("[Task] Failed to process document %s: %s", document_id, exc)
        raise self.retry(exc=exc)


async def _process_document_async(document_id: str, workspace_id: str) -> dict:
    """The actual async processing logic."""
    from src.infrastructure.database.connection import AsyncSessionLocal
    from src.infrastructure.repositories.postgres_document_repository import PostgresDocumentRepository
    from src.infrastructure.document_processor.text_extractor import TextExtractor
    from src.infrastructure.document_processor.chunker import DocumentChunker
    from src.infrastructure.embeddings.ollama_embeddings import OllamaEmbeddingService
    from src.infrastructure.vector_store.qdrant_client import QdrantVectorStore
    from src.domain.entities.document import DocumentStatus
    from src.core.config import settings
    
    async with AsyncSessionLocal() as session:
        doc_repo = PostgresDocumentRepository(session)
        doc = await doc_repo.get_by_id(UUID(document_id))
        
        if not doc:
            raise ValueError(f"Document {document_id} not found")
        
        # Mark as processing
        doc.status = DocumentStatus.PROCESSING
        await doc_repo.update(doc)
        
        try:
            # 1. Extract text
            extractor = TextExtractor()
            text = extractor.extract(doc.file_path, doc.document_type)
            
            # 2. Chunk
            chunker = DocumentChunker()
            chunks = chunker.chunk(
                text=text,
                document_id=doc.id,
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap,
            )
            
            # 3. Embed in batches
            embedding_service = OllamaEmbeddingService()
            texts = [chunk.content for chunk in chunks]
            embeddings = await embedding_service.embed_batch(texts)
            
            # 4. Store in Qdrant
            qdrant = QdrantVectorStore()
            await qdrant.initialize()
            await qdrant.upsert_chunks(chunks, embeddings, str(workspace_id))
            
            # Update embedding IDs on chunks
            for chunk, embedding in zip(chunks, embeddings):
                chunk.embedding_id = str(chunk.id)  # Use chunk UUID as Qdrant point ID
            
            # 5. Save chunks to PostgreSQL
            await doc_repo.save_chunks(chunks)
            
            # 6. Mark document as ready
            doc.status = DocumentStatus.READY
            doc.total_chunks = len(chunks)
            await doc_repo.update(doc)
            
            await session.commit()
            
            return {
                "document_id": document_id,
                "status": "ready",
                "total_chunks": len(chunks),
            }
        
        except Exception as exc:
            # Mark as failed
            doc.status = DocumentStatus.FAILED
            doc.metadata["processing_error"] = str(exc)
            await doc_repo.update(doc)
            await session.commit()
            raise
