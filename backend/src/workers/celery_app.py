"""Celery application for background task processing."""
from celery import Celery
from src.core.config import settings

celery_app = Celery(
    "enterprise_ai",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["src.workers.document_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,  # Retry on worker crash
    worker_prefetch_multiplier=1,  # One task at a time (LLM calls are heavy)
    task_routes={
        "src.workers.document_tasks.process_document": {"queue": "documents"},
    },
    beat_schedule={},
)
