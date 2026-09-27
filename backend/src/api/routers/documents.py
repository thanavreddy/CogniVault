"""Local document management endpoints."""
from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status

from src.documents.manager import DocumentManager
from src.rag.pipeline import RagPipeline

router = APIRouter()


@router.get("")
def list_documents() -> dict:
    return {"documents": DocumentManager().list()}


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile = File(...)) -> dict:
    try:
        return await DocumentManager().save(file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/{filename}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(filename: str) -> None:
    manager = DocumentManager()
    try:
        manager.delete(filename)
        RagPipeline().remove_file(filename)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Document not found") from exc


@router.post("/index")
def index_documents(filename: str | None = Query(default=None)) -> dict:
    manager = DocumentManager()
    try:
        if filename:
            manager.paths(filename)
        result = RagPipeline().index(manager.paths())
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Document not found") from exc
    return {"message": "Documents indexed", **result}
