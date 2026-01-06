# Docuify Backend - Setup Instructions

## Quick Start (Development)

1. **Install dependencies**
   ```bash
   poetry install
   ```

2. **Setup environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start dependencies with Docker**
   ```bash
   docker-compose up -d postgres redis
   ```

4. **Run migrations**
   ```bash
   poetry run alembic upgrade head
   ```

5. **Start the server**
   ```bash
   poetry run uvicorn app.main:app --reload
   ```

6. **Access the API**
   - Swagger Docs: http://localhost:8000/docs
   - Health Check: http://localhost:8000/healthz

## Testing

```bash
poetry run pytest -v
```

## Code Quality

```bash
# Linting
poetry run ruff check app/ tests/

# Formatting
poetry run ruff format app/ tests/

# Type checking
poetry run mypy app/
```

## Next Steps

See README.md for complete documentation and next development milestones.
