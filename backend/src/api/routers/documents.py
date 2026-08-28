"""Document management API endpoints."""
from uuid import UUID
from typing import Optional, List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, status, Query
from pydantic import BaseModel

from src.api.dependencies import (
    CurrentUser, DocumentRepo, VectorStore, EmbeddingService,
)
from src.application.use_cases.document_use_cases import (
    UploadDocumentUseCase,
    GetDocumentsUseCase,
    DeleteDocumentUseCase,
    SearchDocumentsUseCase,
)
from src.core.config import settings

router = APIRouter()


class SearchRequest(BaseModel):
    query: str
    workspace_id: UUID
    top_k: int = 10
    document_ids: Optional[List[UUID]] = None


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    user: CurrentUser,
    doc_repo: DocumentRepo,
    file: UploadFile = File(...),
    workspace_id: UUID = Form(...),
    title: Optional[str] = Form(None),
):
    """Upload a document (PDF, DOCX, TXT, MD). Processing happens asynchronously."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename required")

    # Validate file type
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in settings.supported_file_types_list:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: .{ext}. Supported: {settings.supported_file_types_list}",
        )

    # Validate size
    file_bytes = await file.read()
    if len(file_bytes) > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max: {settings.max_upload_size_mb}MB",
        )

    use_case = UploadDocumentUseCase(doc_repo)
    document = await use_case.execute(
        file_bytes=file_bytes,
        filename=file.filename,
        workspace_id=workspace_id,
        user_id=user.user_id,
        title=title,
    )

    # Redis-backed Celery processing is disabled.

    return {
        "id": str(document.id),
        "title": document.title,
        "file_name": document.file_name,
        "status": document.status.value,
        "file_size": document.file_size,
        "document_type": document.document_type.value,
        "created_at": document.created_at.isoformat(),
        "message": "Document uploaded. Background processing is disabled.",
    }


@router.get("/")
async def list_documents(
    workspace_id: UUID,
    user: CurrentUser,
    doc_repo: DocumentRepo,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    """List documents in a workspace with pagination."""
    use_case = GetDocumentsUseCase(doc_repo)
    documents, total = await use_case.execute(workspace_id, skip, limit)
    return {
        "documents": [
            {
                "id": str(d.id),
                "title": d.title,
                "file_name": d.file_name,
                "file_size": d.file_size,
                "document_type": d.document_type.value,
                "status": d.status.value,
                "total_chunks": d.total_chunks,
                "created_at": d.created_at.isoformat(),
            }
            for d in documents
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/{document_id}")
async def get_document(
    document_id: UUID,
    user: CurrentUser,
    doc_repo: DocumentRepo,
):
    document = await doc_repo.get_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return {
        "id": str(document.id),
        "title": document.title,
        "file_name": document.file_name,
        "file_size": document.file_size,
        "document_type": document.document_type.value,
        "status": document.status.value,
        "total_chunks": document.total_chunks,
        "metadata": document.metadata,
        "created_at": document.created_at.isoformat(),
        "updated_at": document.updated_at.isoformat(),
    }


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    workspace_id: UUID,
    user: CurrentUser,
    doc_repo: DocumentRepo,
    vector_store: VectorStore,
):
    use_case = DeleteDocumentUseCase(doc_repo, vector_store)
    try:
        await use_case.execute(document_id, workspace_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Document not found")
    except PermissionError:
        raise HTTPException(status_code=403, detail="Access denied")


@router.post("/search")
async def search_documents(
    request: SearchRequest,
    user: CurrentUser,
    vector_store: VectorStore,
    embedding_service: EmbeddingService,
):
    """Semantic search across workspace documents."""
    use_case = SearchDocumentsUseCase(vector_store, embedding_service)
    results = await use_case.execute(
        query=request.query,
        workspace_id=request.workspace_id,
        top_k=request.top_k,
        document_ids=request.document_ids,
    )
    return {
        "query": request.query,
        "results": [
            {
                "chunk_id": r.chunk_id,
                "document_id": r.document_id,
                "document_title": r.document_title,
                "content": r.content,
                "score": r.score,
                "page_number": r.page_number,
            }
            for r in results
        ],
        "total": len(results),
    }


@router.get("/{document_id}/chunks")
async def get_document_chunks(
    document_id: UUID,
    user: CurrentUser,
    doc_repo: DocumentRepo,
):
    """Get all chunks for a document."""
    document = await doc_repo.get_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    chunks = await doc_repo.get_chunks_by_document(document_id)
    return {
        "document_id": str(document_id),
        "chunks": [
            {
                "id": str(c.id),
                "chunk_index": c.chunk_index,
                "page_number": c.page_number,
                "token_count": c.token_count,
                "content_preview": c.content[:200] + "..." if len(c.content) > 200 else c.content,
                "has_embedding": c.embedding_id is not None,
            }
            for c in chunks
        ],
        "total": len(chunks),
    }
