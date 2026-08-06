from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from src.domain.entities.document import Document, DocumentChunk

class DocumentRepository(ABC):
    @abstractmethod
    async def get_by_id(self, document_id: UUID) -> Optional[Document]:
        pass

    @abstractmethod
    async def get_by_workspace(self, workspace_id: UUID, skip: int = 0, limit: int = 100) -> List[Document]:
        pass

    @abstractmethod
    async def create(self, document: Document) -> Document:
        pass

    @abstractmethod
    async def update(self, document: Document) -> Document:
        pass

    @abstractmethod
    async def delete(self, document_id: UUID) -> bool:
        pass

    @abstractmethod
    async def get_chunks_by_document(self, document_id: UUID) -> List[DocumentChunk]:
        pass

    @abstractmethod
    async def save_chunks(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        pass

    @abstractmethod
    async def get_chunk_by_id(self, chunk_id: UUID) -> Optional[DocumentChunk]:
        pass
