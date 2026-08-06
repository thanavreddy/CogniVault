#!/bin/bash
set -e

echo "Starting Setup for Enterprise AI Knowledge Assistant..."

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo >&2 "Docker is required but it's not installed. Aborting."; exit 1; }
command -v python >/dev/null 2>&1 || { echo >&2 "Python is required but it's not installed. Aborting."; exit 1; }
command -v node >/dev/null 2>&1 || { echo >&2 "Node is required but it's not installed. Aborting."; exit 1; }

# Copy .env.example if .env doesn't exist
if [ ! -f .env ]; then
    echo "Copying .env.example to .env..."
    cp .env.example .env
else
    echo ".env already exists, skipping copy."
fi

# Pull and start infra
echo "Pulling docker images and starting infrastructure..."
docker compose pull
docker compose up -d postgres qdrant redis

# Wait for health checks
echo "Waiting for PostgreSQL to be ready..."
until docker compose exec postgres pg_isready -U postgres -d ai_assistant; do
    echo "Waiting for database..."
    sleep 2
done

# Backend Setup
echo "Setting up Backend..."
if [ -d "backend" ]; then
    cd backend
    if [ ! -d ".venv" ]; then
        python -m venv .venv
    fi
    source .venv/bin/activate || source .venv/Scripts/activate
    pip install -r requirements.txt || echo "requirements.txt not found, skipping pip install."
    
    echo "Running database migrations..."
    alembic upgrade head || echo "Alembic migrations failed or not set up yet."
    cd ..
else
    echo "Backend directory not found, skipping backend setup."
fi

# Frontend Setup
echo "Setting up Frontend..."
if [ -d "frontend" ]; then
    cd frontend
    npm install
    cd ..
else
    echo "Frontend directory not found, skipping frontend setup."
fi

echo "=================================================="
echo "Setup Complete!"
echo "You can now run 'make dev' or './scripts/run_dev.sh' to start the application."
echo "URLs:"
echo " - Backend API: http://localhost:8000"
echo " - Frontend: http://localhost:3000"
echo " - Grafana: http://localhost:3001"
echo "=================================================="
