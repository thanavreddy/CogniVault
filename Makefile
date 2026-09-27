.PHONY: setup dev test lint-backend lint-frontend format clean

setup:
	bash scripts/setup.sh

dev:
	bash scripts/run_dev.sh

test:
	bash scripts/run_tests.sh

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

