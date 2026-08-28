# CogniVault

CogniVault is an enterprise knowledge assistant that lets authenticated users upload
documents, search their workspace knowledge base, and ask grounded questions about the
retrieved content. LLM inference and embeddings run locally through Ollama.

## Implemented Features

- FastAPI backend with versioned REST endpoints.
- Next.js 15 frontend with Clerk authentication and workspace screens.
- Document upload for PDF, DOCX, TXT, and Markdown files.
- File-size and file-type validation with PostgreSQL document metadata.
- Text extraction and configurable document chunking.
- Local Ollama embeddings using a separate `nomic-embed-text` model.
- Qdrant vector storage with workspace and document filtering.
- Semantic document search with configurable result limits.
- Retrieval-augmented generation using retrieved document context.
- Source citations attached to generated answers.
- Conversation creation, history, message persistence, and deletion.
- Workspace-scoped document and conversation access.
- Clerk JWT validation with a development fallback when authentication is not configured.
- OpenAPI documentation at `/docs` and `/redoc`.

## Architecture

```text
Next.js frontend
        |
        v
FastAPI REST API ---- Clerk authentication
        |
        +---- PostgreSQL: users' workspaces, documents, conversations, messages
        +---- Qdrant: document chunk vectors and metadata
        +---- Ollama: local chat generation and local embeddings
```

The RAG flow is:

```text
Upload -> extract text -> chunk -> Ollama embeddings -> Qdrant
Question -> Ollama embedding -> Qdrant search -> context builder -> Ollama answer -> citations
```

The current implementation uses a provider-neutral RAG pipeline and model-routing
classification. All routing tiers resolve to the configured local Ollama model. The
repository does not currently contain an executable six-agent LangGraph workflow; the
implemented answer path is the RAG pipeline described above.

## Technology Stack

| Area | Technology |
|------|------------|
| Frontend | Next.js 15, React, TypeScript, Tailwind CSS |
| API | FastAPI, Uvicorn, Pydantic |
| Relational data | PostgreSQL, SQLAlchemy, Alembic |
| Vector search | Qdrant |
| Local AI | Ollama, LangChain Ollama integration |
| Authentication | Clerk JWT |
| Testing | Pytest, pytest-asyncio |

## Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Node.js 18+
- Ollama
- The Ollama models used by the application:

```bash
ollama pull qwen2.5:7b
ollama pull nomic-embed-text
ollama serve
```

## Quick Start

1. Copy the root `.env.example` to `.env` and fill in the required Clerk values if authentication is enabled.
2. Copy `backend/.env.example` to `backend/.env` and review the database, Qdrant, and Ollama settings.
3. Start Ollama and pull the models listed above.
4. Start PostgreSQL and Qdrant:

   ```bash
   docker compose up -d postgres qdrant
   ```

5. Install backend and frontend dependencies, then run:

   ```bash
   make setup
   make dev
   ```

6. Open the frontend at http://localhost:3000. The backend API is available at http://localhost:8000.

When the backend runs inside Docker and Ollama runs on the host, set:

```dotenv
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

For a locally running backend, use `http://localhost:11434`.

## Configuration

Backend settings are defined in `backend/.env.example`:

| Variable | Purpose | Default |
|----------|---------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Local PostgreSQL database |
| `QDRANT_HOST` | Qdrant host | `localhost` |
| `QDRANT_PORT` | Qdrant port | `6333` |
| `OLLAMA_BASE_URL` | Ollama server URL | `http://localhost:11434` |
| `OLLAMA_MODEL` | Local chat model | `qwen2.5:7b` |
| `OLLAMA_EMBEDDING_MODEL` | Local embedding model | `nomic-embed-text` |
| `EMBEDDING_DIMENSIONS` | Qdrant vector size | `768` |
| `CHUNK_SIZE` | Maximum chunk size | `1000` |
| `CHUNK_OVERLAP` | Chunk overlap | `200` |
| `MAX_CONTEXT_TOKENS` | RAG context budget | `8000` |
| `CLERK_SECRET_KEY` | Clerk server secret | Empty in development |

No OpenAI or Anthropic API key is required.

## API

The main endpoints are:

- `GET /health`
- `POST /api/v1/documents/upload`
- `GET /api/v1/documents`
- `POST /api/v1/documents/search`
- `GET /api/v1/documents/{document_id}/chunks`
- `POST /api/v1/conversations/{conversation_id}/messages`
- `GET /api/v1/conversations/{conversation_id}/messages`
- `GET /api/v1/workspaces`
- `GET /api/v1/analytics/summary`

See [docs/api-reference.md](docs/api-reference.md) for request and response details.

## Development Commands

```bash
make setup          # Install and initialize local development dependencies
make dev            # Start the backend and frontend
make test           # Run backend tests
make lint-backend   # Run Ruff checks
make lint-frontend  # Run frontend linting
make docker-up      # Start the Docker Compose services
make docker-down    # Stop the Docker Compose services
```

## Embedding Data Migration

The local default embedding model produces 768-dimensional vectors. Existing Qdrant data
created with a different embedding model or dimension cannot be reused directly. Recreate
the Qdrant collection and upload the documents again whenever the embedding model or
dimension changes.


## Why I built this
Why I Built This

How does someone new to a company quickly find information
buried inside large collections of private documents?

CogniVault explores this problem by providing a private,
AI-powered knowledge assistant that lets employees ask
natural-language questions over company documents and
receive grounded answers with citations.

I also wanted to explore an architecture I could eventually
use for CtrlXStudios as it grows.
## Documentation

- [API reference](docs/api-reference.md)
- [Architecture notes](docs/architecture.md)
- [Entity relationship diagram](docs/er-diagram.md)
