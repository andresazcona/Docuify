.PHONY: help install dev test lint format type-check migrate db-upgrade db-downgrade clean docker-up docker-down

help:
	@echo "Docuify Backend - Available Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install       - Install dependencies with Poetry"
	@echo "  make env          - Copy .env.example to .env"
	@echo ""
	@echo "Development:"
	@echo "  make dev          - Run development server with reload"
	@echo "  make docker-up    - Start PostgreSQL, Redis, Qdrant"
	@echo "  make docker-down  - Stop all Docker services"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  make test         - Run all tests"
	@echo "  make test-cov     - Run tests with coverage"
	@echo "  make lint         - Check code with ruff"
	@echo "  make format       - Format code with ruff"
	@echo "  make type-check   - Run mypy type checking"
	@echo "  make check        - Run all checks (lint + type + test)"
	@echo ""
	@echo "Database:"
	@echo "  make migrate      - Create new migration"
	@echo "  make db-upgrade   - Apply migrations"
	@echo "  make db-downgrade - Rollback last migration"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean        - Remove cache and temp files"

install:
	poetry install

env:
	cp .env.example .env
	@echo "Created .env file - Please edit with your configuration"

dev:
	poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

docker-up:
	docker-compose up -d postgres redis qdrant
	@echo "Services started. Waiting for health checks..."
	@sleep 5
	@docker-compose ps

docker-down:
	docker-compose down

test:
	poetry run pytest -v

test-cov:
	poetry run pytest --cov=app --cov-report=html --cov-report=term

lint:
	poetry run ruff check app/ tests/

format:
	poetry run ruff format app/ tests/
	poetry run ruff check --fix app/ tests/

type-check:
	poetry run mypy app/

check: lint type-check test
	@echo "All checks passed!"

migrate:
	@read -p "Enter migration message: " msg; \
	poetry run alembic revision --autogenerate -m "$$msg"

db-upgrade:
	poetry run alembic upgrade head

db-downgrade:
	poetry run alembic downgrade -1

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf htmlcov/ .coverage
	@echo "Cleaned up cache and temp files"
