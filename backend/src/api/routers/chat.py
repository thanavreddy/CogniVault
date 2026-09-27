"""Question answering endpoint."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.rag.pipeline import RagPipeline

router = APIRouter()


class ChatRequest(BaseModel):
    question: str = Field(min_length=1)


@router.post("")
def chat(request: ChatRequest) -> dict:
    try:
        return RagPipeline().ask(request.question)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="RAG services are unavailable. Start Qdrant, Ollama, and index documents first.",
        ) from exc