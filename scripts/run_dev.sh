#!/bin/bash
set -e

echo "Starting development environment..."

# Start infrastructure
docker compose up -d postgres qdrant prometheus grafana jaeger

echo "Waiting for services to be ready..."
sleep 5

# Start backend
echo "Starting backend..."
if [ -d "backend" ]; then
    (cd backend && source .venv/Scripts/activate 2>/dev/null || source .venv/bin/activate 2>/dev/null || true && uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload) &
    BACKEND_PID=$!
else
    echo "Backend not found."
fi

# Start frontend
echo "Starting frontend..."
if [ -d "frontend" ]; then
    (cd frontend && npm run dev) &
    FRONTEND_PID=$!
else
    echo "Frontend not found."
fi

echo "=================================================="
echo "Development servers running!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "Grafana:  http://localhost:3001"
echo "Jaeger:   http://localhost:16686"
echo "Press Ctrl+C to stop all services."
echo "=================================================="

# Wait for processes
wait $BACKEND_PID $FRONTEND_PID
