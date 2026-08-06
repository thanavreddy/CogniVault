from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from typing import List
from uuid import UUID

from src.application.dto.document_dto import DocumentResponse, DocumentListResponse, SearchRequest, SearchResponse
from src.application.use_cases.document_use_cases import UploadDocumentUseCase, GetDocumentsUseCase, DeleteDocumentUseCase, SearchDocumentsUseCase
from src.api.dependencies import get_document_repository
from src.domain.repositories.document_repository import DocumentRepository
# from src.api.middleware.auth import verify_clerk_token

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    workspace_id: UUID,
    file: UploadFile = File(...),
    document_repo: DocumentRepository = Depends(get_document_repository)
    # user = Depends(verify_clerk_token)
):
    # This should inject the DocumentService properly, just scaffolding
    # use_case = UploadDocumentUseCase(document_repo, document_service)
    # return await use_case.execute(file, workspace_id, UUID(user["sub"]))
    raise HTTPException(status_code=501, detail="Not fully implemented in scaffold")

@router.get("", response_model=DocumentListResponse)
async def list_documents(
    workspace_id: UUID,
    skip: int = 0,
    limit: int = 100,
    document_repo: DocumentRepository = Depends(get_document_repository)
):
    use_case = GetDocumentsUseCase(document_repo)
    docs = await use_case.execute(workspace_id, skip, limit)
    
    return DocumentListResponse(
        items=[DocumentResponse(
            id=d.id,
            workspace_id=d.workspace_id,
            title=d.title,
            file_name=d.file_name,
            file_size=d.file_size,
            document_type=d.document_type,
            status=d.status,
            created_at=d.created_at,
            updated_at=d.updated_at
        ) for d in docs],
        total=len(docs), # proper count query needed
        skip=skip,
        limit=limit
    )

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    document_repo: DocumentRepository = Depends(get_document_repository)
):
    use_case = DeleteDocumentUseCase(document_repo)
    success = await use_case.execute(document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
        
@router.post("/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    raise HTTPException(status_code=501, detail="Search implemented in domain layer, router needs service injection")
