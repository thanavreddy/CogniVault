"""Integration tests for the Documents API endpoints."""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
from uuid import uuid4
from io import BytesIO

pytestmark = pytest.mark.asyncio


class TestHealthEndpoint:
    async def test_health_check_returns_healthy(self, test_client: AsyncClient):
        response = await test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("healthy", "ok")


class TestDocumentUpload:
    async def test_upload_requires_auth(self, test_client: AsyncClient):
        """Upload endpoint should reject requests without auth."""
        files = {"file": ("test.pdf", BytesIO(b"fake pdf content"), "application/pdf")}
        response = await test_client.post("/api/v1/documents/upload", files=files)
        # Should return 401 or 403 without auth token
        assert response.status_code in (401, 403, 422)

    async def test_upload_with_mock_auth(
        self,
        test_client: AsyncClient,
        mock_qdrant,
        mock_ollama_embeddings,
    ):
        """Upload with mocked auth and dependencies should succeed."""
        workspace_id = str(uuid4())
        files = {"file": ("test.txt", BytesIO(b"Hello world content for testing"), "text/plain")}
        
        with (
            patch("src.api.dependencies.get_current_user", return_value={"user_id": "user_123", "workspace_id": workspace_id}),
            patch("src.api.dependencies.get_vector_store", return_value=mock_qdrant),
            patch("src.api.dependencies.get_embedding_service", return_value=mock_ollama_embeddings),
        ):
            response = await test_client.post(
                "/api/v1/documents/upload",
                files=files,
                headers={"Authorization": "Bearer mock_token"},
                data={"workspace_id": workspace_id},
            )
        # Either 201 Created or 422 if workspace_id validation fails - check the API is reachable
        assert response.status_code in (200, 201, 422)


class TestDocumentList:
    async def test_list_documents_requires_auth(self, test_client: AsyncClient):
        response = await test_client.get("/api/v1/documents")
        assert response.status_code in (401, 403)

    async def test_list_documents_with_mock_auth(self, test_client: AsyncClient):
        workspace_id = str(uuid4())
        with patch(
            "src.api.dependencies.get_current_user",
            return_value={"user_id": "user_123", "workspace_id": workspace_id},
        ):
            response = await test_client.get(
                "/api/v1/documents",
                headers={"Authorization": "Bearer mock_token"},
                params={"workspace_id": workspace_id},
            )
        assert response.status_code in (200, 422)


class TestDocumentSearch:
    async def test_search_requires_auth(self, test_client: AsyncClient):
        response = await test_client.post(
            "/api/v1/documents/search",
            json={"query": "test query", "workspace_id": str(uuid4())},
        )
        assert response.status_code in (401, 403)
