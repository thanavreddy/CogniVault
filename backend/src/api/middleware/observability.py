"""OpenTelemetry and request tracing middleware."""
import time
import uuid
import logging
import json
from typing import Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

try:
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    OTLP_AVAILABLE = True
except ImportError:
    OTLP_AVAILABLE = False

from src.core.config import settings

logger = logging.getLogger(__name__)


def setup_telemetry() -> None:
    """Initialize OpenTelemetry tracing provider."""
    resource = Resource.create({
        "service.name": settings.otel_service_name,
        "service.version": "1.0.0",
        "deployment.environment": settings.app_env,
    })
    
    provider = TracerProvider(resource=resource)
    
    if OTLP_AVAILABLE:
        try:
            exporter = OTLPSpanExporter(
                endpoint=settings.otel_exporter_otlp_endpoint,
            )
            provider.add_span_processor(BatchSpanProcessor(exporter))
            logger.info("OTel exporter configured → %s", settings.otel_exporter_otlp_endpoint)
        except Exception as e:
            logger.warning("Could not set up OTLP exporter: %s", e)
    
    trace.set_tracer_provider(provider)


class RequestTracingMiddleware(BaseHTTPMiddleware):
    """Add request_id to every request and log latency."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Attach request_id to request state
        request.state.request_id = request_id
        
        # Get tracer
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span(
            f"{request.method} {request.url.path}",
            attributes={
                "http.method": request.method,
                "http.url": str(request.url),
                "http.route": request.url.path,
                "request.id": request_id,
            },
        ) as span:
            try:
                response = await call_next(request)
                duration_ms = (time.time() - start_time) * 1000
                
                span.set_attribute("http.status_code", response.status_code)
                span.set_attribute("http.response_time_ms", duration_ms)
                
                # Add request ID to response headers
                response.headers["X-Request-ID"] = request_id
                
                # Log request
                logger.info(
                    "request completed",
                    extra={
                        "request_id": request_id,
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": response.status_code,
                        "duration_ms": round(duration_ms, 2),
                    },
                )
                return response
            
            except Exception as exc:
                duration_ms = (time.time() - start_time) * 1000
                span.record_exception(exc)
                span.set_attribute("error", True)
                logger.error(
                    "request failed",
                    extra={
                        "request_id": request_id,
                        "method": request.method,
                        "path": request.url.path,
                        "duration_ms": round(duration_ms, 2),
                        "error": str(exc),
                    },
                    exc_info=True,
                )
                raise


def add_tracing_middleware(app: FastAPI) -> None:
    """Register all observability middleware on the FastAPI app."""
    setup_telemetry()
    app.add_middleware(RequestTracingMiddleware)
    
    # FastAPI auto-instrumentation
    try:
        FastAPIInstrumentor.instrument_app(app)
    except Exception as e:
        logger.warning("FastAPI instrumentor failed: %s", e)
