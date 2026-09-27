from pathlib import Path

import pytest

from src.core.config import settings
from src.documents.manager import DocumentManager


def test_document_manager_lists_supported_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "documents_dir", str(tmp_path))
    manager = DocumentManager()
    (tmp_path / "notes.md").write_text("hello", encoding="utf-8")
    (tmp_path / "ignored.csv").write_text("ignored", encoding="utf-8")

    assert [item["filename"] for item in manager.list()] == ["notes.md"]