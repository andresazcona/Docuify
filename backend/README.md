# Docuify backend

FastAPI service behind [Docuify](../README.md): document ingestion, hybrid retrieval and cited answers.

## Run

```bash
pip install -e ".[embeddings]" pytest pytest-asyncio ruff httpx
uvicorn app.main:app --reload        # http://localhost:8000/docs
pytest -q
ruff check . && ruff format --check .
```

Settings come from environment variables (see `.env.example`). The defaults run on SQLite with keyword retrieval and extractive answers, so nothing else is needed to try it.

## Layout

```
app/
  api/v1/       documents, chats (plain and SSE), meta
  core/         settings, errors with trace ids, structured logging, SSRF and filename guards
  db/           async SQLAlchemy session and models (documents, chunks, chats, messages)
  rag/          extract · chunking · retrieval (BM25 + cosine, RRF) · answer · llm · embeddings
  services/     ingestion, chat, document management
tests/          unit (retrieval, answers, providers with mocked HTTP) and API tests with real PDFs
scripts/        make_samples.py writes the two sample handbooks
postman/        Postman collection for the API
```

## Configuration highlights

| Variable | Default | Meaning |
|---|---|---|
| `DATABASE_URL` | SQLite file | `postgresql+asyncpg://…` in Docker |
| `EMBEDDING_PROVIDER` | `none` | `fastembed` turns on local dense retrieval |
| `EMBEDDING_MODEL` | multilingual MiniLM | Any fastembed model |
| `LLM_PROVIDER` | `extractive` | `anthropic`, `openai` or `ollama` for every request |
| `LLM_BASE_URL` | unset | OpenAI-compatible server, operator only |
| `ALLOW_CLIENT_LLM_KEYS` | `true` | Let a request bring its own key in `X-LLM-Key` |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | `600` / `100` | Characters per chunk |
| `RAG_TOP_K` | `5` | Passages used per question |
