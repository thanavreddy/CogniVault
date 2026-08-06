import os
from typing import List, Dict, Any
from uuid import UUID
from dataclasses import dataclass
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

from src.domain.entities.document import DocumentChunk

@dataclass
class SearchResult:
    chunk_id: UUID
    document_id: UUID
    score: float
    payload: Dict[str, Any]

class QdrantVectorStore:
    def __init__(self):
        self.host = os.getenv("QDRANT_HOST", "localhost")
        self.port = int(os.getenv("QDRANT_PORT", "6333"))
        self.api_key = os.getenv("QDRANT_API_KEY")
        self.collection_name = os.getenv("QDRANT_COLLECTION_NAME", "knowledge_base")
        self.dimensions = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))
        
        self.client = AsyncQdrantClient(host=self.host, port=self.port, api_key=self.api_key)

    async def initialize(self):
        # Create collection if it doesn't exist
        collections = await self.client.get_collections()
        if not any(c.name == self.collection_name for c in collections.collections):
            await self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=self.dimensions, distance=Distance.COSINE)
            )

    async def upsert_chunks(self, chunks: List[DocumentChunk], embeddings: List[List[float]]) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks and embeddings must match")

        points = []
        for chunk, embedding in zip(chunks, embeddings):
            payload = chunk.metadata.copy()
            payload.update({
                "document_id": str(chunk.document_id),
                "chunk_index": chunk.chunk_index,
                "page_number": chunk.page_number,
                "content": chunk.content
            })
            
            points.append(
                PointStruct(
                    id=str(chunk.id),
                    vector=embedding,
                    payload=payload
                )
            )

        if points:
            await self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )

    async def search(self, query_embedding: List[float], workspace_id: UUID, top_k: int = 5, filters: Dict[str, Any] = None) -> List[SearchResult]:
        
        # Base filter for workspace
        query_filter = Filter(
            must=[
                FieldCondition(
                    key="workspace_id",
                    match=MatchValue(value=str(workspace_id))
                )
            ]
        )

        if filters:
            for k, v in filters.items():
                query_filter.must.append(
                    FieldCondition(key=k, match=MatchValue(value=v))
                )

        search_result = await self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            query_filter=query_filter,
            limit=top_k
        )

        return [
            SearchResult(
                chunk_id=UUID(hit.id),
                document_id=UUID(hit.payload.get("document_id")),
                score=hit.score,
                payload=hit.payload
            ) for hit in search_result
        ]

    async def delete_by_document(self, document_id: UUID) -> None:
        await self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=str(document_id))
                    )
                ]
            )
        )
