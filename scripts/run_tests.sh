#!/bin/bash
set -e

echo "Running tests..."

# Run Backend Tests
if [ -d "backend" ]; then
    echo "Running backend tests..."
    cd backend
    source .venv/Scripts/activate 2>/dev/null || source .venv/bin/activate 2>/dev/null || true
    pytest --cov=src --cov-report=term-missing tests/ || echo "Backend tests failed or missing."
    cd ..
fi

# Run Frontend Tests
if [ -d "frontend" ]; then
    echo "Running frontend tests..."
    cd frontend
    npm run test || echo "Frontend tests failed or not configured."
    cd ..
fi

echo "Test run completed."
