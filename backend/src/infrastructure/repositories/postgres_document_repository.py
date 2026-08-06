from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from src.domain.entities.document import Document, DocumentChunk
from src.domain.repositories.document_repository import DocumentRepository
from src.infrastructure.database.models.document_model import DocumentModel, DocumentChunkModel

class PostgresDocumentRepository(DocumentRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_entity(self, model: DocumentModel) -> Document:
        return Document(
            id=model.id,
            workspace_id=model.workspace_id,
            user_id=model.user_id,
            title=model.title,
            file_name=model.file_name,
            file_path=model.file_path,
            file_size=model.file_size,
            document_type=model.document_type,
            status=model.status,
            total_chunks=model.total_chunks,
            metadata=model.metadata_,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def _to_chunk_entity(self, model: DocumentChunkModel) -> DocumentChunk:
        return DocumentChunk(
            id=model.id,
            document_id=model.document_id,
            content=model.content,
            chunk_index=model.chunk_index,
            page_number=model.page_number,
            token_count=model.token_count,
            embedding_id=model.embedding_id,
            metadata=model.metadata_
        )

    async def get_by_id(self, document_id: UUID) -> Optional[Document]:
        result = await self.session.execute(
            select(DocumentModel).where(DocumentModel.id == document_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_workspace(self, workspace_id: UUID, skip: int = 0, limit: int = 100) -> List[Document]:
        result = await self.session.execute(
            select(DocumentModel)
            .where(DocumentModel.workspace_id == workspace_id)
            .offset(skip)
            .limit(limit)
            .order_by(DocumentModel.created_at.desc())
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def create(self, document: Document) -> Document:
        model = DocumentModel(
            id=document.id,
            workspace_id=document.workspace_id,
            user_id=document.user_id,
            title=document.title,
            file_name=document.file_name,
            file_path=document.file_path,
            file_size=document.file_size,
            document_type=document.document_type,
            status=document.status,
            total_chunks=document.total_chunks,
            metadata_=document.metadata,
            created_at=document.created_at,
            updated_at=document.updated_at
        )
        self.session.add(model)
        await self.session.flush()
        return self._to_entity(model)

    async def update(self, document: Document) -> Document:
        result = await self.session.execute(
            select(DocumentModel).where(DocumentModel.id == document.id)
        )
        model = result.scalar_one_or_none()
        if model:
            model.status = document.status
            model.total_chunks = document.total_chunks
            model.metadata_ = document.metadata
            await self.session.flush()
            return self._to_entity(model)
        raise ValueError(f"Document {document.id} not found")

    async def delete(self, document_id: UUID) -> bool:
        result = await self.session.execute(
            delete(DocumentModel).where(DocumentModel.id == document_id)
        )
        await self.session.flush()
        return result.rowcount > 0

    async def get_chunks_by_document(self, document_id: UUID) -> List[DocumentChunk]:
        result = await self.session.execute(
            select(DocumentChunkModel)
            .where(DocumentChunkModel.document_id == document_id)
            .order_by(DocumentChunkModel.chunk_index.asc())
        )
        return [self._to_chunk_entity(m) for m in result.scalars().all()]

    async def save_chunks(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        models = [
            DocumentChunkModel(
                id=c.id,
                document_id=c.document_id,
                content=c.content,
                chunk_index=c.chunk_index,
                page_number=c.page_number,
                token_count=c.token_count,
                embedding_id=c.embedding_id,
                metadata_=c.metadata
            )
            for c in chunks
        ]
        self.session.add_all(models)
        await self.session.flush()
        return [self._to_chunk_entity(m) for m in models]

    async def get_chunk_by_id(self, chunk_id: UUID) -> Optional[DocumentChunk]:
        result = await self.session.execute(
            select(DocumentChunkModel).where(DocumentChunkModel.id == chunk_id)
        )
        model = result.scalar_one_or_none()
        return self._to_chunk_entity(model) if model else None
