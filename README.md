# Enterprise AI Knowledge Assistant

## Overview
A production-grade Enterprise AI Knowledge Assistant demonstrating:
- RAG Pipeline with semantic & hybrid retrieval
- Multi-Agent System with LangGraph (6 agents)
- Evaluation Framework with 6 metrics
- Guardrails (injection, hallucination, moderation)
- Full Observability (OpenTelemetry + AgentOps)
- Dynamic Model Routing across local Ollama query complexity tiers

## Architecture
```
[Frontend: Next.js 15]
       ↓
[FastAPI Backend]
       ↓
[LangGraph Multi-Agent Pipeline]
  ├── Planner Agent
  ├── Retriever Agent  
  ├── Research Agent
  ├── Writer Agent
  ├── Critic Agent
  └── Guardrail Agent
       ↓
[Qdrant Vector DB] + [PostgreSQL]
```

## Tech Stack
| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | Next.js 15, React, Tailwind CSS | UI and Client App |
| Backend | FastAPI, Python 3.11 | API and Orchestration |
| Database | PostgreSQL 16, SQLAlchemy | Relational Data |
| Vector DB | Qdrant | Embedding Storage and Semantic Search |
| Caching/Queue | Disabled | Redis caching and background tasks are disabled |
| LLM | Ollama | Local LLM inference with Ollama |
| AI Framework | LangGraph, LangChain | Multi-Agent Orchestration |
| Auth | Clerk | Identity Management |
| Observability | Prometheus, Grafana, Jaeger | Monitoring and Tracing |

## Prerequisites
- Docker & Docker Compose
- Node.js 18+
- Python 3.11+
- Ollama (running locally)

## Quick Start
1. Clone the repository
2. Install Ollama, then download the models:
       `ollama pull qwen2.5:7b`
       `ollama pull nomic-embed-text`
3. Start Ollama with `ollama serve`
4. Run `make setup`, then `make dev`
5. Open http://localhost:3000

## Project Structure
- `/backend`: FastAPI Python backend
- `/frontend`: Next.js web application
- `/monitoring`: Prometheus and Grafana configurations
- `/scripts`: Setup and utility scripts
- `/docs`: Architecture and API documentation

## API Reference
Please refer to [API Reference](docs/api-reference.md).

## Environment Variables
| Variable | Description |
|----------|-------------|
| POSTGRES_URL | Connection string for PostgreSQL |
| QDRANT_URL | Connection URL for Qdrant |
| OLLAMA_BASE_URL | Ollama server URL; use `http://host.docker.internal:11434` when the backend runs in Docker |
| OLLAMA_MODEL | Local chat model, default `qwen2.5:7b` |
| OLLAMA_EMBEDDING_MODEL | Separate local embedding model, default `nomic-embed-text` |
| NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY | Clerk public key for auth |

## Architecture Decisions
See [Architecture](docs/architecture.md).

The AI path is local: Ollama -> LangChain -> LangGraph/RAG agents -> FastAPI. The same
Ollama model is used for routing tiers, while `nomic-embed-text` is used separately for
Qdrant embeddings. Native tool calling is available through `OllamaLLMClient.bind_tools`
when supported by the selected model; `qwen2.5` supports tool calling. Structured output
is exposed through `OllamaLLMClient.with_structured_output`.

Changing from the previous 1536-dimensional cloud embeddings to 768-dimensional local
embeddings requires recreating or re-indexing the Qdrant collection. Stop the app, remove
the Qdrant data volume (`docker compose down -v`), then start it and re-upload documents.

## Development Guide
Use the `Makefile` commands to manage the environment:
- `make docker-up`
- `make lint-backend`
- `make lint-frontend`

## Testing
Run tests using `make test`.

## Contributing
Please follow the standard Git flow and submit PRs with linked issues.
