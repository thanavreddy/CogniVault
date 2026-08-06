from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import os

from src.infrastructure.database.connection import create_tables, engine
from src.infrastructure.vector_store.qdrant_client import QdrantVectorStore
from src.api.middleware.observability import add_tracing_middleware
from src.api.routers import documents, conversations, workspaces, analytics, health

logger = logging.getLogger(__name__)

API_V1_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — runs startup and shutdown logic."""
    # ── Startup ──────────────────────────────────────────────────────────────
    logger.info("Starting Enterprise AI Knowledge Assistant...")
    await create_tables()
    qdrant = QdrantVectorStore()
    await qdrant.initialize()
    logger.info("Startup complete. Services ready.")
    yield
    # ── Shutdown ─────────────────────────────────────────────────────────────
    logger.info("Shutting down...")
    await engine.dispose()


app = FastAPI(
    title="Enterprise AI Knowledge Assistant",
    description=(
        "Production-grade RAG backend with multi-agent orchestration, "
        "evaluation framework, guardrails, and full observability."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ── CORS ─────────────────────────────────────────────────────────────────────
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Observability middleware ──────────────────────────────────────────────────
add_tracing_middleware(app)

# ── Exception handlers ───────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error", "detail": str(exc)},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
    )

# ── Routers ──────────────────────────────────────────────────────────────────
app.include_router(health.router, tags=["Health"])
app.include_router(documents.router,     prefix=f"{API_V1_PREFIX}/documents",     tags=["Documents"])
app.include_router(conversations.router, prefix=f"{API_V1_PREFIX}/conversations", tags=["Conversations"])
app.include_router(workspaces.router,    prefix=f"{API_V1_PREFIX}/workspaces",    tags=["Workspaces"])
app.include_router(analytics.router,     prefix=f"{API_V1_PREFIX}/analytics",     tags=["Analytics"])
