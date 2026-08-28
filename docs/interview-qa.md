# Phase 1: Architecture - Interview Q&A

## System Design Questions

**Q: Why did you choose Clean Architecture for the backend?**
A: Clean architecture separates concerns into concentric layers, ensuring the core business logic (Domain/Application) has no dependencies on external frameworks, databases, or UIs (Infrastructure/API). This makes the system highly testable, maintainable, and adaptable to future changes. If we ever need to swap out FastAPI for another framework, or change vector databases from Qdrant to Pinecone, our core logic remains untouched.

**Q: Why FastAPI over Django or Flask?**
A: FastAPI offers native async/await support, which is critical for I/O bound tasks like calling LLM APIs and databases in parallel. It integrates seamlessly with Pydantic for robust request validation and automatically generates OpenAPI (Swagger) documentation, improving frontend-backend collaboration. Its performance matches Node/Go frameworks in web serving.

**Q: Why PostgreSQL + Qdrant instead of just a single vector database?**
A: Different data access patterns require different tools. Relational databases like PostgreSQL are excellent for transactional integrity, structured metadata queries, RBAC, and complex relational joins (Users, Workspaces, Chat history). Qdrant is optimized strictly for high-dimensional vector similarity search. Combining them allows us to handle both complex relational queries and semantic search effectively.

**Q: How does your authentication system work?**
A: We use Clerk for identity management. The frontend obtains a JWT upon user login. This token is passed in the `Authorization` header to FastAPI. FastAPI uses a middleware to validate the JWT signature against Clerk's JWKS (JSON Web Key Set), ensuring the request is authenticated and extracting the user ID to enforce workspace-level authorization.

**Q: How would you scale this system?**
A: 
- **Stateless API:** Scale FastAPI horizontally using Kubernetes or ECS behind a load balancer.
- **Database:** Implement connection pooling (PgBouncer), read replicas for PostgreSQL.
- **Async Workers:** Background processing is disabled while Redis-backed workers are disabled.
- **Caching:** Embeddings are requested directly without Redis caching.
- **LLM:** Local inference runs through Ollama; no OpenAI or Anthropic API key is required.

**Q: What's your database indexing strategy?**
A: We use composite indexes (e.g., `workspace_id` + `created_at`) to optimize dashboard queries. Partial indexes are used for tracking document statuses (e.g., `WHERE status = 'processing'`). In Qdrant, HNSW indexes are utilized, along with payload indexes for metadata filtering (like filtering chunks by a specific `document_id`).

**Q: How do you handle database migrations in production?**
A: We use Alembic to manage database schema versions. Migrations are run as part of a CI/CD pipeline using a deployment strategy that separates schema changes from code deployments (blue-green deployments). We ensure migrations are backward compatible (e.g., adding a column before code uses it, dropping it only after code stops using it).

**Q: Why Docker Compose for development?**
A: It provides a reproducible, isolated environment that mirrors production dependencies. New developers can spin up the entire stack (PostgreSQL, Qdrant, and APM tools) with a single `docker compose up` command, eliminating "works on my machine" issues and complicated local setup instructions.

## RAG System Questions

**Q: What is RAG and why is it better than fine-tuning for this use case?**
A: RAG (Retrieval-Augmented Generation) fetches contextually relevant data from a proprietary knowledge base and provides it to the LLM at inference time. It's better than fine-tuning because it prevents hallucination by anchoring answers to factual sources, allows for easy updates of knowledge (just insert/delete documents), and enables strict access control (retrieval is scoped to the user's permissions).

**Q: How do you choose chunk size?**
A: Chunk size is a balance between context completeness and noise. We typically use 500-1000 tokens with a 10-20% overlap to maintain sentence continuity. Smaller chunks yield precise semantic matches, while larger chunks provide better context for the LLM. 

**Q: What is hybrid retrieval?**
A: Hybrid retrieval combines semantic (vector-based) search, which understands intent and meaning, with lexical (keyword-based) search like BM25, which is excellent for exact noun or acronym matching. The results are re-ranked using techniques like Reciprocal Rank Fusion (RRF) to provide the most relevant context.

**Q: How do you handle context window limits?**
A: We limit the number of retrieved chunks (Top-K), summarize lengthy contexts using a map-reduce summarization chain before passing it to the final prompt, and utilize model dynamic routing across the configured local Ollama model.

## AI Engineering Questions

**Q: What is the difference between semantic search and keyword search?**
A: Keyword search looks for exact string matches or variations (e.g., matching "car" to "cars"). Semantic search understands the underlying meaning by mapping text to high-dimensional vectors, allowing it to match "automobile" to "car" even if the exact words are not shared.

**Q: How do embeddings work?**
A: Embeddings are numerical arrays (vectors) that represent the semantic meaning of text. Neural networks (like `text-embedding-3-small`) are trained to place vectors of similar concepts close together in a multi-dimensional space, enabling similarity calculations using cosine distance.

**Q: What is hallucination and how do you detect it?**
A: Hallucination occurs when an LLM confidently generates false or fabricated information. We detect it using a Critic Agent in our LangGraph pipeline that evaluates the generated answer strictly against the retrieved context, scoring its faithfulness and grounding.

**Q: What are guardrails in AI systems?**
A: Guardrails are automated checks that intercept inputs and outputs to ensure safety and compliance. They prevent prompt injection (malicious user inputs attempting to hijack the system), filter toxic content, ensure outputs remain on-topic, and block the exposure of PII (Personally Identifiable Information).
