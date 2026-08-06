from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from src.domain.entities.document import DocumentType, DocumentStatus

class DocumentUploadRequest(BaseModel):
    workspace_id: UUID
    # file handled by FastAPI UploadFile

class DocumentResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    title: str
    file_name: str
    file_size: int
    document_type: DocumentType
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime

class DocumentListResponse(BaseModel):
    items: List[DocumentResponse]
    total: int
    skip: int
    limit: int

class ChunkResponse(BaseModel):
    id: UUID
    document_id: UUID
    content: str
    page_number: Optional[int]
    metadata: Dict[str, Any]

class SearchRequest(BaseModel):
    query: str
    workspace_id: UUID
    filters: Optional[Dict[str, Any]] = None
    limit: int = 5

class SearchResponse(BaseModel):
    results: List[ChunkResponse]
    query_time_ms: int
