import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from src.api.main import app
from src.infrastructure.database.connection import Base, get_db
from src.domain.entities.document import Document, DocumentStatus, DocumentType, DocumentChunk
from src.domain.entities.conversation import Conversation, Message, MessageRole
from src.domain.entities.workspace import Workspace, WorkspacePlan

# Test database URL (SQLite for speed, or override with TEST_DATABASE_URL env)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop_policy():
    import asyncio
    return asyncio.DefaultEventLoopPolicy()


@pytest_asyncio.fixture(scope="function")
async def async_session():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_client(async_session):
    async def override_get_db():
        yield async_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_workspace_id():
    return uuid4()


@pytest.fixture
def sample_user_id():
    return "user_clerk_test_123"


@pytest.fixture
def sample_workspace(sample_workspace_id, sample_user_id):
    return Workspace(
        id=sample_workspace_id,
        name="Test Workspace",
        slug="test-workspace",
        owner_id=sample_user_id,
        plan=WorkspacePlan.FREE,
    )


@pytest.fixture
def sample_document(sample_workspace_id, sample_user_id):
    return Document(
        workspace_id=sample_workspace_id,
        user_id=sample_user_id,
        title="Test Document",
        file_name="test.pdf",
        file_path="/uploads/test.pdf",
        file_size=1024,
        document_type=DocumentType.PDF,
        status=DocumentStatus.READY,
        total_chunks=5,
    )


@pytest.fixture
def sample_chunk(sample_document):
    return DocumentChunk(
        document_id=sample_document.id,
        content="This is a test chunk with sample content for testing purposes.",
        chunk_index=0,
        page_number=1,
        token_count=15,
    )


@pytest.fixture
def sample_conversation(sample_workspace_id, sample_user_id):
    return Conversation(
        workspace_id=sample_workspace_id,
        user_id=sample_user_id,
        title="Test Conversation",
    )


@pytest.fixture
def mock_qdrant():
    mock = AsyncMock()
    mock.search.return_value = []
    mock.upsert_chunks.return_value = None
    mock.delete_by_document.return_value = None
    return mock


@pytest.fixture
def mock_ollama_embeddings():
    mock = AsyncMock()
    mock.embed_text.return_value = [0.1] * 1536
    mock.embed_batch.return_value = [[0.1] * 1536]
    return mock


@pytest.fixture
def mock_ollama_client():
    mock = AsyncMock()
    from src.infrastructure.llm.ollama_client import LLMResponse
    mock.complete.return_value = LLMResponse(
        content="This is a test answer from the mock LLM.",
        model="qwen2.5:7b",
        usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        cost=0.0001,
        latency_ms=500,
    )
    return mock
