# System Architecture

## Overview
The Enterprise AI Knowledge Assistant is built with a microservices-inspired monolithic architecture using Clean Architecture principles on the backend. It integrates a LangGraph multi-agent pipeline for advanced RAG operations.

## Clean Architecture Layers
### Domain Layer
Contains enterprise logic, entities (User, Document, Message, Workspace), and repository interfaces. Agnostic to frameworks.

### Application Layer  
Contains use cases (e.g., ProcessDocument, AnswerQuery). Orchestrates the flow of data to and from the entities, directing those entities to use their enterprise logic to achieve the goals of the use case.

### Infrastructure Layer
Implements repository interfaces. Handles database connections (SQLAlchemy), vector database interactions (Qdrant), LLM integrations (LangChain/OpenAI), and external APIs.

### API Layer
FastAPI endpoints routing HTTP requests to application use cases. Handles authentication middlewares, request validation (Pydantic), and response formatting.

## Data Flow
1. **Client Request**: Frontend sends a request to FastAPI.
2. **Middleware**: Auth token validated via Clerk.
3. **Controller**: FastAPI validates payload using Pydantic.
4. **Use Case**: Application layer executes business logic.
5. **Infrastructure**: Database/LLM calls are made.
6. **Response**: Data is returned through the layers back to the client.

## Database Design
PostgreSQL is used for relational data (Workspaces, Users, Documents metadata, Chat history). See ER Diagram for schema details.

## Vector Store Design
Qdrant is used to store document chunks and embeddings. Collections are indexed with HNSW for fast similarity search, partitioned by workspace for tenant isolation.

## Agent Architecture
LangGraph implements a multi-agent system:
- **Planner Agent**: Deconstructs queries.
- **Retriever Agent**: Generates search queries.
- **Research Agent**: Performs iterative deep-dive retrieval.
- **Writer Agent**: Synthesizes information into answers.
- **Critic Agent**: Reviews for factual accuracy.
- **Guardrail Agent**: Ensures compliance and safety.

## Security Architecture
- JWT-based Auth (Clerk)
- Row-Level Security via Workspace ID isolation in application logic
- Input validation and sanitization
- Guardrail agent for preventing prompt injection and toxic outputs

## Observability Architecture
- **Metrics**: Prometheus scraping FastAPI metrics (request duration, counts, etc.).
- **Dashboards**: Grafana visualizing Prometheus data.
- **Tracing**: OpenTelemetry auto-instrumentation sending traces to Jaeger.
- **Agent Logging**: AgentOps integration for LLM-specific observability.
