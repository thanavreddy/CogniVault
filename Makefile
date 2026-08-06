.PHONY: setup dev test docker-up docker-down docker-build migrate migrate-create lint-backend lint-frontend format clean logs shell-backend

setup:
	bash scripts/setup.sh

dev:
	bash scripts/run_dev.sh

test:
	bash scripts/run_tests.sh

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-build:
	docker compose build

migrate:
	cd backend && alembic upgrade head

migrate-create:
	cd backend && alembic revision --autogenerate -m "$(M)"

lint-backend:
	cd backend && ruff check src

lint-frontend:
	cd frontend && npm run lint

format:
	cd backend && ruff format src

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".next" -exec rm -rf {} +
	find . -type d -name "node_modules" -exec rm -rf {} +

logs:
	docker compose logs -f

shell-backend:
	docker compose exec backend bash
