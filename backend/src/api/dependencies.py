"""FastAPI dependency helpers for local document storage."""
from src.documents.manager import DocumentManager


def get_document_manager() -> DocumentManager:
    return DocumentManager()
