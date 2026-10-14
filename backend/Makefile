.PHONY: help install dev test lint format check samples clean

help:
	@echo "Folio backend"
	@echo "  make install   install the package with the local-embeddings extra and dev tools"
	@echo "  make dev       run the API with reload on :8000"
	@echo "  make test      run the test suite"
	@echo "  make lint      ruff check + format check"
	@echo "  make format    apply ruff formatting"
	@echo "  make check     lint + tests"
	@echo "  make samples   regenerate ../samples/*.pdf"
	@echo "Whole stack: docker compose up --build (from the repository root)"

install:
	pip install -e ".[embeddings]" pytest pytest-asyncio pytest-cov ruff httpx

dev:
	uvicorn app.main:app --reload --port 8000

test:
	pytest -q

lint:
	ruff check .
	ruff format --check .

format:
	ruff check . --fix
	ruff format .

check: lint test

samples:
	python scripts/make_samples.py

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache .coverage htmlcov dev.db
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
