# CogniVault

CogniVault is a small, local-first RAG application. Next.js calls FastAPI, which uses LangChain loaders and prompting, FastEmbed embeddings, Qdrant retrieval, and Ollama for local answers. Original files stay in `data/documents`; Qdrant stores only chunks and metadata.

## Prerequisites

- Python 3.11+
- Node.js 18+
- Qdrant at `http://localhost:6333`
- Ollama at `http://localhost:11434`

Pull the chat model before starting Ollama:

```bash
ollama pull qwen2.5:7b
ollama serve
```

## Quick Start

1. Copy `backend/.env.example` to `backend/.env` and adjust local service URLs if needed.
2. Install dependencies and start both applications:

   ```bash
   make setup
   make dev
   ```

3. Open `http://localhost:3000`.

The Documents screen uploads files to `data/documents`, indexes them into Qdrant, and supports deletion or re-indexing. The Chat screen retrieves relevant chunks and returns the answer with source filenames and chunk IDs.

## API

- `GET /health`
- `GET /documents`
- `POST /documents/upload`
- `DELETE /documents/{filename}`
- `POST /documents/index`
- `POST /chat`

## Configuration

See `backend/.env.example` for `DOCUMENTS_DIR`, Qdrant, Ollama, FastEmbed, and chunking settings.

## Development Commands

```bash
make setup
make dev
make test
make lint-backend
make lint-frontend
```
