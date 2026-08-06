from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from uuid import UUID
from src.domain.entities.document import Document, DocumentChunk

class DocumentService(ABC):
    @abstractmethod
    async def process_document(self, document: Document) -> Document:
        pass

    @abstractmethod
    async def search_documents(
        self, 
        workspace_id: UUID, 
        query: str, 
        filters: Optional[Dict[str, Any]] = None
    ) -> List[DocumentChunk]:
        pass
