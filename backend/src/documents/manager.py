"""Store source documents in the local filesystem."""
from __future__ import annotations
from pathlib import Path

from fastapi import UploadFile

from src.core.config import settings

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".markdown"}


class DocumentManager:
    def __init__(self) -> None:
        self.directory = Path(settings.documents_dir).resolve()
        self.directory.mkdir(parents=True, exist_ok=True)

    def list(self) -> list[dict]:
        return [self._metadata(path) for path in sorted(self.directory.iterdir()) if self._is_document(path)]

    async def save(self, upload: UploadFile) -> dict:
        filename = Path(upload.filename or "").name
        path = self._path_for(filename)
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise ValueError("Supported file types: PDF, DOCX, TXT, and Markdown")
        contents = await upload.read()
        if len(contents) > settings.max_upload_size_mb * 1024 * 1024:
            raise ValueError(f"File too large. Maximum size is {settings.max_upload_size_mb} MB")
        path.write_bytes(contents)
        return self._metadata(path)

    def delete(self, filename: str) -> Path:
        path = self._path_for(filename)
        if not path.is_file():
            raise FileNotFoundError(filename)
        path.unlink()
        return path

    def paths(self, filename: str | None = None) -> list[Path]:
        if filename:
            path = self._path_for(filename)
            if not path.is_file():
                raise FileNotFoundError(filename)
            return [path]
        return [path for path in sorted(self.directory.iterdir()) if self._is_document(path)]

    def _path_for(self, filename: str) -> Path:
        path = (self.directory / Path(filename).name).resolve()
        if path.parent != self.directory:
            raise ValueError("Invalid filename")
        return path

    @staticmethod
    def _is_document(path: Path) -> bool:
        return path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS

    def _metadata(self, path: Path) -> dict:
        stat = path.stat()
        return {
            "filename": path.name,
            "file_type": path.suffix.lower().lstrip("."),
            "file_path": str(path),
            "size": stat.st_size,
            "modified_at": stat.st_mtime,
        }