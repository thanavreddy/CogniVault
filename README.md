# CogniVault - Enterprise AI Knowledge Assistant

> **Production-oriented AI knowledge assistant built with RAG, multi-agent workflows, and modern full-stack engineering.**

An end-to-end AI application that allows users to ask questions over private enterprise documents and receive grounded, context-aware answers.

The project combines **RAG, LangGraph multi-agent workflows, LLMs, evaluation, guardrails** into a complete full-stack system.

---

##  Highlights

*  **RAG Pipeline** — Semantic and hybrid document retrieval
*  **Multi-Agent AI** — 6-agent workflow built with LangGraph
*  **LLM Integration** — OpenAI and Anthropic models with dynamic routing
*  **AI Guardrails** — Prompt injection, hallucination, and moderation checks
*  **Evaluation** — 6-metric evaluation framework for measuring response quality
*  **Full-Stack Application** — Next.js frontend with FastAPI backend
*  **Authentication** — Secure user authentication with Clerk

---

##  Architecture

```text
                    ┌─────────────────────┐
                    │   Next.js / React   │
                    │      Frontend       │
                    └──────────┬──────────┘
                               │
                          REST API
                               │
                    ┌──────────▼──────────┐
                    │   FastAPI Backend   │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │ LangGraph Workflow  │
                    │                     │
                    │ Planner             │
                    │ Retriever           │
                    │ Researcher          │
                    │ Writer              │
                    │ Critic              │
                    │ Guardrails          │
                    └───────┬───────┬─────┘
                            │       │
                   ┌────────▼──┐ ┌──▼──────────┐
                   │  Qdrant   │ │ PostgreSQL  │
                   │ Vector DB │ │  Database   │
                   └───────────┘ └─────────────┘
```

### AI Workflow

```text
User Question
      ↓
Planner
      ↓
Retriever
      ↓
Researcher
      ↓
Writer
      ↓
Critic
      ↓
Guardrails
      ↓
Grounded Answer
```

---

## Tech Stack

| Area                | Technologies                                         |
| ------------------- | ---------------------------------------------------- |
| **AI / Agents**     | LangGraph, LangChain, OpenAI,                        |
| **Backend**         | Python, FastAPI                                      |
| **Frontend**        | Next.js, React, Tailwind CSS                         |
| **Database**        | PostgreSQL, SQLAlchemy                               |
| **Vector Search**   | Qdrant                                               |
| **Authentication**  | Clerk                                                |
| **Infrastructure**  | Docker, Docker Compose                               |

---

##  Multi-Agent System

The application uses specialized agents instead of relying on a single LLM call.

| Agent          | Responsibility                                     |
| -------------- | -------------------------------------------------- |
| **Planner**    | Breaks the user's request into actionable steps    |
| **Retriever**  | Finds relevant information from the knowledge base |
| **Researcher** | Processes and synthesizes retrieved context        |
| **Writer**     | Generates the final response                       |
| **Critic**     | Reviews the generated answer                       |
| **Guardrail**  | Checks for unsafe or unreliable outputs            |

This architecture allows individual stages to be evaluated and improved independently.

---

## RAG Pipeline

The knowledge assistant uses a retrieval-augmented generation pipeline to ground responses in enterprise documents.

```text
Documents
    ↓
Document Processing
    ↓
Chunking & Embeddings
    ↓
Qdrant
    ↓
Semantic / Hybrid Retrieval
    ↓
Relevant Context
    ↓
LLM
    ↓
Grounded Response
```

The retrieved context is passed to the LLM so responses can be generated using information from the organization's knowledge base.

---

## AI Safety & Reliability

The system includes multiple layers designed to improve reliability:

* Prompt injection detection
* Hallucination checks
* Content moderation
* Critic-based response evaluation
* Automated evaluation metrics
* LLM/model routing

---

##  Evaluation & Observability

The project includes an evaluation framework with **6 metrics** to measure the quality of generated responses.

The system also provides visibility into AI workflows through:

* OpenTelemetry
* AgentOps
* Prometheus
* Grafana
* Jaeger

This makes it possible to inspect requests, trace agent workflows, and monitor system behavior.

---

## Dynamic Model Routing

Different models can be selected based on the requirements of a request.

**Supported models:**

* GPT-4.1-mini
* GPT-4.1

This allows the system to balance capability and cost depending on the task.

---

##  Project Structure

```text
.
├── backend/        # FastAPI backend & AI orchestration
├── frontend/       # Next.js application
├── monitoring/     # Monitoring & observability configuration
├── scripts/        # Setup and utility scripts
└── docs/            # Architecture & API documentation
```

---

##  Getting Started

### Prerequisites

* Docker & Docker Compose
* Node.js 18+
* Python 3.11+
* OpenAI API key

### Setup

```bash
git clone https://github.com/thanavreddy/CogniVault.git
cd CogniVault

make setup
make dev
```

Then open:

```text
http://localhost:3000
```

---

##  Environment Variables

Create your environment configuration with the required services:

```env
POSTGRES_URL=
QDRANT_URL=

OPENAI_API_KEY=
ANTHROPIC_API_KEY=

NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=
```

---

##  Testing

Run the test suite with:

```bash
make test
```

Useful development commands:

```bash
make docker-up
make lint-backend
make lint-frontend
```

---

## Documentation

* [Architecture](docs/architecture.md)
* [API Reference](docs/api-reference.md)

---

##  Why I Built This

I was curious about a simple problem:

How does someone new to a company quickly find the information they need?

A new employee might need one small piece of information buried inside a large collection of private company documents. Asking coworkers every time isn't practical, while manually searching through large documents can be slow and frustrating.

That led me to build this project as an AI-powered internal knowledge assistant — a system where employees can ask questions in natural language and get answers grounded in the organization's private knowledge base.

I also wanted to build something that I could eventually use for CtrlXStudios if I grow it into a larger organization, where keeping company knowledge accessible and useful would become increasingly important.

This project was my way of exploring what that system could look like while learning how to build a complete AI application around RAG, agents, evaluation, guardrails, and observability.

---
