from typing import List
from uuid import UUID
import tiktoken
from langchain.text_splitter import RecursiveCharacterTextSplitter

from src.domain.entities.document import DocumentChunk

class DocumentChunker:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=self._token_length,
            separators=["\n\n", "\n", " ", ""]
        )
        self.encoding = tiktoken.get_encoding("cl100k_base")

    def _token_length(self, text: str) -> int:
        return len(self.encoding.encode(text))

    def chunk(self, text: str, document_id: UUID) -> List[DocumentChunk]:
        texts = self.splitter.split_text(text)
        chunks = []
        
        for i, chunk_text in enumerate(texts):
            token_count = self._token_length(chunk_text)
            
            # Simple page estimation for formats without native pages
            estimated_page = (i * self.chunk_size) // 2000 + 1
            
            chunk = DocumentChunk(
                document_id=document_id,
                content=chunk_text,
                chunk_index=i,
                page_number=estimated_page,
                token_count=token_count,
                metadata={"length": len(chunk_text)}
            )
            chunks.append(chunk)
            
        return chunks
