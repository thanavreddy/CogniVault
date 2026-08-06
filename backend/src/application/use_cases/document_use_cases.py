from typing import List, Optional, Dict, Any
from uuid import UUID
import os
import aiofiles
from fastapi import UploadFile

from src.domain.entities.document import Document, DocumentType, DocumentStatus, DocumentChunk
from src.domain.repositories.document_repository import DocumentRepository
from src.domain.services.document_service import DocumentService

class UploadDocumentUseCase:
    def __init__(self, document_repository: DocumentRepository, document_service: DocumentService):
        self.document_repository = document_repository
        self.document_service = document_service

    async def execute(self, file: UploadFile, workspace_id: UUID, user_id: UUID) -> Document:
        # Create uploads directory if it doesn't exist
        os.makedirs("uploads", exist_ok=True)
        file_path = f"uploads/{workspace_id}_{file.filename}"
        
        # Save file to disk
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)

        file_size = os.path.getsize(file_path)
        
        # Determine type
        ext = file.filename.split('.')[-1].lower()
        doc_type_map = {
            'pdf': DocumentType.PDF,
            'docx': DocumentType.DOCX,
            'txt': DocumentType.TXT,
            'md': DocumentType.MARKDOWN
        }
        document_type = doc_type_map.get(ext, DocumentType.TXT)

        document = Document(
            workspace_id=workspace_id,
            user_id=user_id,
            title=file.filename,
            file_name=file.filename,
            file_path=file_path,
            file_size=file_size,
            document_type=document_type
        )
        
        # Save initial document
        document = await self.document_repository.create(document)
        
        # Trigger async processing (in a real system this would use Celery/Redis)
        # For this setup, we just process it directly or assume a background task picks it up
        await self.document_service.process_document(document)
        
        return document

class GetDocumentsUseCase:
    def __init__(self, document_repository: DocumentRepository):
        self.document_repository = document_repository

    async def execute(self, workspace_id: UUID, skip: int = 0, limit: int = 100) -> List[Document]:
        return await self.document_repository.get_by_workspace(workspace_id, skip, limit)

class DeleteDocumentUseCase:
    def __init__(self, document_repository: DocumentRepository):
        self.document_repository = document_repository

    async def execute(self, document_id: UUID) -> bool:
        # NOTE: Also need to delete from vector store and remove file in a full implementation
        return await self.document_repository.delete(document_id)

class SearchDocumentsUseCase:
    def __init__(self, document_service: DocumentService):
        self.document_service = document_service

    async def execute(self, workspace_id: UUID, query: str, filters: Optional[Dict[str, Any]] = None) -> List[DocumentChunk]:
        return await self.document_service.search_documents(workspace_id, query, filters)
