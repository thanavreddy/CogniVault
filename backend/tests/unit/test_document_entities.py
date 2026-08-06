"""Unit tests for Document domain entities."""
import pytest
from uuid import uuid4
from datetime import datetime, timezone

from src.domain.entities.document import (
    Document,
    DocumentChunk,
    DocumentStatus,
    DocumentType,
)


class TestDocumentStatus:
    def test_status_values(self):
        assert DocumentStatus.PENDING == "PENDING"
        assert DocumentStatus.PROCESSING == "PROCESSING"
        assert DocumentStatus.READY == "READY"
        assert DocumentStatus.FAILED == "FAILED"

    def test_status_is_string_enum(self):
        assert isinstance(DocumentStatus.READY, str)


class TestDocumentType:
    def test_type_values(self):
        assert DocumentType.PDF == "PDF"
        assert DocumentType.DOCX == "DOCX"
        assert DocumentType.TXT == "TXT"
        assert DocumentType.MARKDOWN == "MARKDOWN"


class TestDocument:
    def test_create_document_with_defaults(self):
        workspace_id = uuid4()
        user_id = "user_123"
        doc = Document(
            workspace_id=workspace_id,
            user_id=user_id,
            title="Annual Report 2024",
            file_name="annual_report_2024.pdf",
            file_path="/uploads/annual_report_2024.pdf",
            file_size=2_048_000,
            document_type=DocumentType.PDF,
        )
        assert doc.id is not None
        assert doc.workspace_id == workspace_id
        assert doc.user_id == user_id
        assert doc.status == DocumentStatus.PENDING
        assert doc.total_chunks == 0
        assert doc.metadata == {}
        assert isinstance(doc.created_at, datetime)
        assert doc.created_at.tzinfo is not None  # Must be timezone-aware

    def test_document_is_ready_false_by_default(self):
        doc = Document(
            workspace_id=uuid4(),
            user_id="user_123",
            title="Test",
            file_name="test.pdf",
            file_path="/test.pdf",
            file_size=1024,
            document_type=DocumentType.PDF,
        )
        assert doc.is_ready() is False

    def test_document_is_ready_true_when_ready(self):
        doc = Document(
            workspace_id=uuid4(),
            user_id="user_123",
            title="Test",
            file_name="test.pdf",
            file_path="/test.pdf",
            file_size=1024,
            document_type=DocumentType.PDF,
            status=DocumentStatus.READY,
        )
        assert doc.is_ready() is True

    def test_get_file_extension_pdf(self):
        doc = Document(
            workspace_id=uuid4(),
            user_id="user_123",
            title="Test",
            file_name="report.pdf",
            file_path="/report.pdf",
            file_size=1024,
            document_type=DocumentType.PDF,
        )
        assert doc.get_file_extension() == "pdf"

    def test_get_file_extension_no_extension(self):
        doc = Document(
            workspace_id=uuid4(),
            user_id="user_123",
            title="Test",
            file_name="noextension",
            file_path="/noextension",
            file_size=1024,
            document_type=DocumentType.TXT,
        )
        assert doc.get_file_extension() == ""

    def test_unique_ids_per_document(self):
        workspace_id = uuid4()
        doc1 = Document(
            workspace_id=workspace_id,
            user_id="user_123",
            title="Doc 1",
            file_name="doc1.pdf",
            file_path="/doc1.pdf",
            file_size=1024,
            document_type=DocumentType.PDF,
        )
        doc2 = Document(
            workspace_id=workspace_id,
            user_id="user_123",
            title="Doc 2",
            file_name="doc2.pdf",
            file_path="/doc2.pdf",
            file_size=1024,
            document_type=DocumentType.PDF,
        )
        assert doc1.id != doc2.id

    def test_metadata_is_mutable_per_instance(self):
        doc1 = Document(
            workspace_id=uuid4(), user_id="u1", title="T1",
            file_name="f1.pdf", file_path="/f1.pdf", file_size=1,
            document_type=DocumentType.PDF,
        )
        doc2 = Document(
            workspace_id=uuid4(), user_id="u2", title="T2",
            file_name="f2.pdf", file_path="/f2.pdf", file_size=1,
            document_type=DocumentType.PDF,
        )
        doc1.metadata["key"] = "value"
        assert "key" not in doc2.metadata  # No shared state


class TestDocumentChunk:
    def test_create_chunk(self):
        document_id = uuid4()
        chunk = DocumentChunk(
            document_id=document_id,
            content="This is a sample chunk of text extracted from a document.",
            chunk_index=0,
            page_number=1,
            token_count=12,
        )
        assert chunk.id is not None
        assert chunk.document_id == document_id
        assert chunk.chunk_index == 0
        assert chunk.token_count == 12
        assert chunk.embedding_id is None

    def test_chunk_default_metadata(self):
        chunk = DocumentChunk(
            document_id=uuid4(),
            content="Content",
            chunk_index=1,
        )
        assert chunk.metadata == {}
        assert chunk.token_count == 0
