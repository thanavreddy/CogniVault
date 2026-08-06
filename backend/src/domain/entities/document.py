from enum import Enum
from typing import Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class DocumentStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"

class DocumentType(str, Enum):
    PDF = "PDF"
    DOCX = "DOCX"
    TXT = "TXT"
    MARKDOWN = "MARKDOWN"

class DocumentChunk(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    document_id: UUID
    content: str
    chunk_index: int
    page_number: Optional[int] = None
    token_count: int = 0
    embedding_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Document(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    workspace_id: UUID
    user_id: UUID
    title: str
    file_name: str
    file_path: str
    file_size: int
    document_type: DocumentType
    status: DocumentStatus = DocumentStatus.PENDING
    total_chunks: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    def is_ready(self) -> bool:
        return self.status == DocumentStatus.READY
        
    def get_file_extension(self) -> str:
        if "." in self.file_name:
            return self.file_name.rsplit(".", 1)[1].lower()
        return ""
