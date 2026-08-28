"""Qdrant vector store — manages collections and hybrid retrieval."""
import logging
from uuid import UUID
from dataclasses import dataclass, field
from typing import Optional, Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    Range,
    SearchRequest,
    ScoredPoint,
    UpdateStatus,
    CreateCollection,
    PayloadSchemaType,
)
from qdrant_client.http.exceptions import UnexpectedResponse

from src.core.config import settings
from src.domain.entities.document import DocumentChunk

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """A single vector search result with metadata."""
    chunk_id: str
    document_id: str
    workspace_id: str
    score: float
    content: str
    document_title: str = ""
    page_number: Optional[int] = None
    chunk_index: int = 0
    metadata: dict = field(default_factory=dict)


class QdrantVectorStore:
    """Async Qdrant client with collection lifecycle management."""

    def __init__(self) -> None:
        self._client: Optional[AsyncQdrantClient] = None
        self.collection_name = settings.qdrant_collection_name
        self.vector_size = settings.embedding_dimensions

    @property
    def client(self) -> AsyncQdrantClient:
        if self._client is None:
            raise RuntimeError("QdrantVectorStore not initialized. Call initialize() first.")
        return self._client

    async def initialize(self) -> None:
        """Connect to Qdrant and ensure the collection exists."""
        self._client = AsyncQdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
            api_key=settings.qdrant_api_key,
        )
        await self._ensure_collection()
        logger.info(
            "QdrantVectorStore initialized: %s:%s collection=%s",
            settings.qdrant_host,
            settings.qdrant_port,
            self.collection_name,
        )

    async def _ensure_collection(self) -> None:
        """Create the collection if it doesn't already exist."""
        try:
            await self.client.get_collection(self.collection_name)
            logger.info("Collection '%s' already exists.", self.collection_name)
        except Exception:
            # Collection doesn't exist — create it
            await self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE,
                ),
            )
            # Create payload indexes for efficient filtering
            await self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="workspace_id",
                field_schema=PayloadSchemaType.KEYWORD,
            )
            await self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="document_id",
                field_schema=PayloadSchemaType.KEYWORD,
            )
            logger.info("Created collection '%s' with dim=%d.", self.collection_name, self.vector_size)

    async def upsert_chunks(
        self,
        chunks: list[DocumentChunk],
        embeddings: list[list[float]],
        workspace_id: str,
        document_title: str = "",
    ) -> None:
        """Upsert document chunks with their embeddings into Qdrant."""
        if len(chunks) != len(embeddings):
            raise ValueError(f"Chunks ({len(chunks)}) and embeddings ({len(embeddings)}) count mismatch")

        points = [
            PointStruct(
                id=str(chunk.id),  # Use chunk UUID as point ID
                vector=embedding,
                payload={
                    "chunk_id": str(chunk.id),
                    "document_id": str(chunk.document_id),
                    "workspace_id": workspace_id,
                    "content": chunk.content,
                    "chunk_index": chunk.chunk_index,
                    "page_number": chunk.page_number,
                    "token_count": chunk.token_count,
                    "document_title": document_title,
                    **chunk.metadata,
                },
            )
            for chunk, embedding in zip(chunks, embeddings)
        ]

        # Upsert in batches of 100
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i : i + batch_size]
            operation_info = await self.client.upsert(
                collection_name=self.collection_name,
                points=batch,
            )
            if operation_info.status != UpdateStatus.COMPLETED:
                raise RuntimeError(f"Qdrant upsert failed: {operation_info.status}")
        
        logger.info(
            "Upserted %d chunks for document %s into Qdrant",
            len(chunks),
            str(chunks[0].document_id) if chunks else "none",
        )

    def _build_filter(
        self,
        workspace_id: str,
        document_ids: Optional[list[str]] = None,
    ) -> Filter:
        """Build a Qdrant filter for workspace isolation and optional document filtering."""
        conditions = [
            FieldCondition(
                key="workspace_id",
                match=MatchValue(value=workspace_id),
            )
        ]
        
        if document_ids:
            conditions.append(
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=document_ids[0]),  # Simplified for single doc
                )
            )
        
        return Filter(must=conditions)

    async def search(
        self,
        query_embedding: list[float],
        workspace_id: str,
        top_k: int = 10,
        document_ids: Optional[list[str]] = None,
        score_threshold: float = 0.5,
    ) -> list[SearchResult]:
        """Semantic search: find top-k most similar chunks."""
        query_filter = self._build_filter(workspace_id, document_ids)
        
        hits: list[ScoredPoint] = await self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            query_filter=query_filter,
            limit=top_k,
            score_threshold=score_threshold,
            with_payload=True,
        )
        
        results = [
            SearchResult(
                chunk_id=hit.payload.get("chunk_id", str(hit.id)),
                document_id=hit.payload.get("document_id", ""),
                workspace_id=hit.payload.get("workspace_id", ""),
                score=hit.score,
                content=hit.payload.get("content", ""),
                document_title=hit.payload.get("document_title", ""),
                page_number=hit.payload.get("page_number"),
                chunk_index=hit.payload.get("chunk_index", 0),
            )
            for hit in hits
        ]
        
        logger.debug(
            "Qdrant search: workspace=%s top_k=%d → %d results",
            workspace_id, top_k, len(results),
        )
        return results

    async def delete_by_document(self, document_id: str) -> None:
        """Remove all vectors belonging to a document."""
        await self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id),
                    )
                ]
            ),
        )
        logger.info("Deleted vectors for document %s from Qdrant", document_id)

    async def delete_by_workspace(self, workspace_id: str) -> None:
        """Remove all vectors for a workspace."""
        await self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="workspace_id",
                        match=MatchValue(value=workspace_id),
                    )
                ]
            ),
        )
        logger.info("Deleted all vectors for workspace %s", workspace_id)

    async def health_check(self) -> dict:
        """Check Qdrant connectivity and collection stats."""
        try:
            info = await self.client.get_collection(self.collection_name)
            return {
                "status": "healthy",
                "vectors_count": info.vectors_count,
                "indexed_vectors_count": info.indexed_vectors_count,
                "points_count": info.points_count,
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def scroll_all(
        self,
        workspace_id: str,
        limit: int = 100,
    ) -> list[SearchResult]:
        """Scroll through all points for a workspace (for batch operations)."""
        results = []
        offset = None
        
        while True:
            records, next_offset = await self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=self._build_filter(workspace_id),
                limit=limit,
                offset=offset,
                with_payload=True,
            )
            
            for record in records:
                results.append(SearchResult(
                    chunk_id=record.payload.get("chunk_id", str(record.id)),
                    document_id=record.payload.get("document_id", ""),
                    workspace_id=workspace_id,
                    score=1.0,
                    content=record.payload.get("content", ""),
                    document_title=record.payload.get("document_title", ""),
                    page_number=record.payload.get("page_number"),
                    chunk_index=record.payload.get("chunk_index", 0),
                ))
            
            if next_offset is None:
                break
            offset = next_offset
        
        return results
