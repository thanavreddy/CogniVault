"""Document management use cases."""
import logging
import os
from pathlib import Path
from uuid import UUID, uuid4
from datetime import datetime, timezone

from src.domain.entities.document import Document, DocumentStatus, DocumentType
from src.domain.repositories.document_repository import DocumentRepository
from src.infrastructure.vector_store.qdrant_client import QdrantVectorStore
from src.core.config import settings

logger = logging.getLogger(__name__)

EXT_TO_TYPE = {
    "pdf": DocumentType.PDF,
    "docx": DocumentType.DOCX,
    "doc": DocumentType.DOCX,
    "txt": DocumentType.TXT,
    "md": DocumentType.MARKDOWN,
    "markdown": DocumentType.MARKDOWN,
}


class UploadDocumentUseCase:
    """Save uploaded file and create a Document record."""

    def __init__(
        self,
        document_repo: DocumentRepository,
    ) -> None:
        self._repo = document_repo

    async def execute(
        self,
        file_bytes: bytes,
        filename: str,
        workspace_id: UUID,
        user_id: str,
        title: str | None = None,
    ) -> Document:
        ext = Path(filename).suffix.lstrip(".").lower()
        if ext not in EXT_TO_TYPE:
            raise ValueError(f"Unsupported file type: .{ext}. Supported: {list(EXT_TO_TYPE.keys())}")

        document_type = EXT_TO_TYPE[ext]

        # Save file to upload directory
        upload_dir = Path(settings.upload_dir) / str(workspace_id)
        upload_dir.mkdir(parents=True, exist_ok=True)

        doc_id = uuid4()
        safe_name = f"{doc_id}_{filename}"
        file_path = upload_dir / safe_name
        file_path.write_bytes(file_bytes)

        document = Document(
            id=doc_id,
            workspace_id=workspace_id,
            user_id=user_id,
            title=title or Path(filename).stem.replace("_", " ").replace("-", " ").title(),
            file_name=filename,
            file_path=str(file_path),
            file_size=len(file_bytes),
            document_type=document_type,
            status=DocumentStatus.PENDING,
        )

        created = await self._repo.create(document)
        logger.info("Uploaded document %s to %s", created.id, file_path)
        return created


class GetDocumentsUseCase:
    def __init__(self, document_repo: DocumentRepository) -> None:
        self._repo = document_repo

    async def execute(
        self,
        workspace_id: UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Document], int]:
        documents = await self._repo.get_by_workspace(workspace_id, skip, limit)
        total = await self._repo.count_by_workspace(workspace_id)
        return documents, total


class DeleteDocumentUseCase:
    def __init__(
        self,
        document_repo: DocumentRepository,
        vector_store: QdrantVectorStore,
    ) -> None:
        self._repo = document_repo
        self._vector_store = vector_store

    async def execute(self, document_id: UUID, workspace_id: UUID) -> None:
        document = await self._repo.get_by_id(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")
        if document.workspace_id != workspace_id:
            raise PermissionError("Document does not belong to this workspace")

        # Delete from Qdrant first
        await self._vector_store.delete_by_document(str(document_id))

        # Delete file from disk
        try:
            if os.path.exists(document.file_path):
                os.remove(document.file_path)
        except OSError as e:
            logger.warning("Could not delete file %s: %s", document.file_path, e)

        # Delete from DB (chunks cascade)
        await self._repo.delete(document_id)
        logger.info("Deleted document %s", document_id)


class SearchDocumentsUseCase:
    def __init__(
        self,
        vector_store: QdrantVectorStore,
        embedding_service,
    ) -> None:
        from src.application.rag.retriever import Retriever
        self._retriever = Retriever(vector_store, embedding_service)

    async def execute(
        self,
        query: str,
        workspace_id: UUID,
        top_k: int = 10,
        document_ids: list[UUID] | None = None,
    ):
        results = await self._retriever.retrieve(
            query=query,
            workspace_id=str(workspace_id),
            top_k=top_k,
            document_ids=[str(d) for d in document_ids] if document_ids else None,
        )
        return results
