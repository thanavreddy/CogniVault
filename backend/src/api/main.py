"""FastAPI application for the local-first CogniVault RAG app."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers import chat, documents, health

app = FastAPI(
    title="CogniVault",
    description="A local-first document question-answering API.",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health.router, tags=["Health"])
app.include_router(documents.router, prefix="/documents", tags=["Documents"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
