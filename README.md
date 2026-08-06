# Enterprise AI Knowledge Assistant

## Overview
A production-grade Enterprise AI Knowledge Assistant demonstrating:
- RAG Pipeline with semantic & hybrid retrieval
- Multi-Agent System with LangGraph (6 agents)
- Evaluation Framework with 6 metrics
- Guardrails (injection, hallucination, moderation)
- Full Observability (OpenTelemetry + AgentOps)
- Dynamic Model Routing (GPT-4.1-mini / GPT-4.1 / Claude)

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
| Caching/Queue | Redis 7 | Caching and Background Tasks |
| AI Framework | LangGraph, LangChain | Multi-Agent Orchestration |
| Auth | Clerk | Identity Management |
| Observability | Prometheus, Grafana, Jaeger | Monitoring and Tracing |

## Prerequisites
- Docker & Docker Compose
- Node.js 18+
- Python 3.11+
- OpenAI API Key

## Quick Start
1. Clone the repository
2. Run `make setup`
3. Run `make dev`
4. Open http://localhost:3000

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
| REDIS_URL | Connection URL for Redis |
| OPENAI_API_KEY | OpenAI API Key |
| ANTHROPIC_API_KEY | Anthropic API Key |
| NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY | Clerk public key for auth |

## Architecture Decisions
See [Architecture](docs/architecture.md).

## Development Guide
Use the `Makefile` commands to manage the environment:
- `make docker-up`
- `make lint-backend`
- `make lint-frontend`

## Testing
Run tests using `make test`.

## Contributing
Please follow the standard Git flow and submit PRs with linked issues.
