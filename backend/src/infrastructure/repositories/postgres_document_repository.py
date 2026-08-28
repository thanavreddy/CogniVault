"""PostgreSQL implementation of the DocumentRepository."""
from uuid import UUID
from typing import Optional
from datetime import datetime, timezone
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload

from src.domain.entities.document import Document, DocumentChunk, DocumentStatus, DocumentType
from src.domain.repositories.document_repository import DocumentRepository
from src.infrastructure.database.models.document_model import DocumentModel, DocumentChunkModel

logger = logging.getLogger(__name__)


class PostgresDocumentRepository(DocumentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Mapping helpers ──────────────────────────────────────────────────────
    @staticmethod
    def _to_entity(model: DocumentModel) -> Document:
        return Document(
            id=model.id,
            workspace_id=model.workspace_id,
            user_id=model.user_id,
            title=model.title,
            file_name=model.file_name,
            file_path=model.file_path,
            file_size=model.file_size,
            document_type=DocumentType(model.document_type),
            status=DocumentStatus(model.status),
            total_chunks=model.total_chunks,
            metadata=model.metadata_ or {},
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _chunk_to_entity(model: DocumentChunkModel) -> DocumentChunk:
        return DocumentChunk(
            id=model.id,
            document_id=model.document_id,
            content=model.content,
            chunk_index=model.chunk_index,
            page_number=model.page_number,
            token_count=model.token_count or 0,
            embedding_id=model.embedding_id,
            metadata=model.metadata_ or {},
        )

    @staticmethod
    def _to_model(entity: Document) -> DocumentModel:
        return DocumentModel(
            id=entity.id,
            workspace_id=entity.workspace_id,
            user_id=entity.user_id,
            title=entity.title,
            file_name=entity.file_name,
            file_path=entity.file_path,
            file_size=entity.file_size,
            document_type=entity.document_type.value,
            status=entity.status.value,
            total_chunks=entity.total_chunks,
            metadata_=entity.metadata,
        )

    # ── Repository methods ───────────────────────────────────────────────────
    async def get_by_id(self, document_id: UUID) -> Optional[Document]:
        result = await self._session.execute(
            select(DocumentModel).where(DocumentModel.id == document_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_workspace(
        self,
        workspace_id: UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Document]:
        result = await self._session.execute(
            select(DocumentModel)
            .where(DocumentModel.workspace_id == workspace_id)
            .order_by(DocumentModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def count_by_workspace(self, workspace_id: UUID) -> int:
        result = await self._session.execute(
            select(func.count(DocumentModel.id))
            .where(DocumentModel.workspace_id == workspace_id)
        )
        return result.scalar_one() or 0

    async def create(self, document: Document) -> Document:
        model = self._to_model(document)
        self._session.add(model)
        await self._session.flush()  # Get DB-generated values without full commit
        await self._session.refresh(model)
        logger.info("Created document: %s (workspace=%s)", model.id, model.workspace_id)
        return self._to_entity(model)

    async def update(self, document: Document) -> Document:
        await self._session.execute(
            update(DocumentModel)
            .where(DocumentModel.id == document.id)
            .values(
                title=document.title,
                status=document.status.value,
                total_chunks=document.total_chunks,
                metadata_=document.metadata,
                updated_at=datetime.now(timezone.utc),
            )
        )
        await self._session.flush()
        updated = await self.get_by_id(document.id)
        return updated

    async def delete(self, document_id: UUID) -> bool:
        result = await self._session.execute(
            delete(DocumentModel).where(DocumentModel.id == document_id)
        )
        await self._session.flush()
        deleted = result.rowcount > 0
        if deleted:
            logger.info("Deleted document: %s", document_id)
        return deleted

    async def get_chunks_by_document(self, document_id: UUID) -> list[DocumentChunk]:
        result = await self._session.execute(
            select(DocumentChunkModel)
            .where(DocumentChunkModel.document_id == document_id)
            .order_by(DocumentChunkModel.chunk_index)
        )
        models = result.scalars().all()
        return [self._chunk_to_entity(m) for m in models]

    async def save_chunks(self, chunks: list[DocumentChunk]) -> list[DocumentChunk]:
        models = [
            DocumentChunkModel(
                id=chunk.id,
                document_id=chunk.document_id,
                content=chunk.content,
                chunk_index=chunk.chunk_index,
                page_number=chunk.page_number,
                token_count=chunk.token_count,
                embedding_id=chunk.embedding_id,
                metadata_=chunk.metadata,
            )
            for chunk in chunks
        ]
        self._session.add_all(models)
        await self._session.flush()
        logger.info("Saved %d chunks for document %s", len(chunks), chunks[0].document_id if chunks else "none")
        return [self._chunk_to_entity(m) for m in models]

    async def get_chunk_by_id(self, chunk_id: UUID) -> Optional[DocumentChunk]:
        result = await self._session.execute(
            select(DocumentChunkModel).where(DocumentChunkModel.id == chunk_id)
        )
        model = result.scalar_one_or_none()
        return self._chunk_to_entity(model) if model else None

    async def update_chunk_embedding_id(self, chunk_id: UUID, embedding_id: str) -> None:
        await self._session.execute(
            update(DocumentChunkModel)
            .where(DocumentChunkModel.id == chunk_id)
            .values(embedding_id=embedding_id)
        )
        await self._session.flush()
