from fastapi import FastAPI
import os
import uuid
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

# If using real OTel:
# from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
# from opentelemetry import trace

class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        start_time = time.time()
        
        # In a real app we'd add this to structlog context
        request.state.request_id = request_id
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        
        return response

def add_tracing_middleware(app: FastAPI):
    app.add_middleware(ObservabilityMiddleware)
    
    # Setup OpenTelemetry if endpoint is provided
    otel_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if otel_endpoint:
        pass # FastAPIInstrumentor.instrument_app(app)
