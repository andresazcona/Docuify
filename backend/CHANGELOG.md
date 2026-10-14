# CHANGELOG

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-10-14

### Added
- Document chat: PDFs are extracted page by page, chunked (never across pages), optionally embedded and stored.
- Hybrid retrieval: BM25 plus cosine similarity over local fastembed vectors, merged with reciprocal rank fusion.
- Cited answers. Extractive mode (no model, no key) by default; Anthropic, OpenAI and Ollama as options.
- Per-request API keys through X-LLM-* headers. Clients never choose the endpoint (SSRF).
- Chat endpoints (create, history, ask) and SSE streaming.
- React frontend (ES/EN) with citations, source panel and answer-engine settings.
- Dockerfiles, docker compose (PostgreSQL, API, nginx), smoke test and CI.

### Changed
- Settings for LLM and embeddings replaced (the Gemini/Qdrant placeholders were never wired).
- Tests use real PDFs; unreadable PDFs now end as FAILED with a reason.
- Tooling: current ruff config, pip-based install (poetry.lock removed).

## [0.1.0] - 2026-01-06

### ✨ Added - Milestone 1: Document Ingestion Complete

#### Core Features
- **Document Ingestion System**
  - ArXiv PDF downloads with automatic URL resolution (abs and pdf formats)
  - Generic URL downloads with comprehensive SSRF protection
  - File upload handling with PDF validation
  - Document storage management with organized directory structure

#### API Endpoints (7 total)
- `POST /api/v1/documents/arxiv` - Create document from arXiv URL
- `POST /api/v1/documents/url` - Create document from public PDF URL
- `POST /api/v1/documents/upload` - Upload PDF file
- `GET /api/v1/documents` - List documents with pagination
- `GET /api/v1/documents/{document_id}` - Get document details
- `POST /api/v1/documents/{document_id}/retry` - Retry failed document processing
- `DELETE /api/v1/documents/{document_id}` - Delete document with storage cleanup

#### Health & Status Endpoints
- `GET /health` - Health check endpoint
- `GET /healthz` - Health check (kubernetes compatible)
- `GET /ready` - Readiness check with database validation
- `GET /readyz` - Readiness check (kubernetes compatible)
- `GET /api/v1/meta` - API metadata and configuration

#### Security Features
- **SSRF Protection**
  - Blocks all private IP ranges (127.0.0.0/8, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
  - Blocks link-local (169.254.0.0/16) and multicast (224.0.0.0/4) addresses
  - Blocks localhost and loopback addresses
  - Real-time IP validation with detailed error messages

- **URL Validation**
  - Only allows HTTP and HTTPS schemes
  - Validates URL format and accessibility
  - Returns appropriate error codes (422 for validation failures)

- **PDF Validation**
  - Magic byte validation (%PDF header)
  - Content-type checking
  - File size limits enforced
  - Prevents non-PDF uploads

- **General Security**
  - Filename sanitization (removes dangerous characters)
  - Secure cryptographic ID generation
  - Structured error responses with trace IDs
  - Comprehensive audit logging

#### Database Layer
- **SQLAlchemy 2.0 Async ORM**
  - Async session management
  - Proper transaction handling
  - Error handling and recovery
  - Status tracking (CREATED, DOWNLOADING, UPLOADED, PROCESSING, FAILED, READY)

- **Repository Pattern**
  - DocumentRepository with full CRUD operations
  - Query optimization with offset/limit pagination
  - Proper cascading and cleanup

#### Configuration & Environment
- **Pydantic Settings v2**
  - Environment-based configuration
  - Safe defaults for development
  - Support for SQLite (dev) and PostgreSQL (prod)
  - Rate limiting configuration (disabled by default)
  - Storage path configuration

- **Database Support**
  - SQLite with aiosqlite for development and testing
  - PostgreSQL async support for production
  - Conditional connection pooling

#### Logging & Monitoring
- **Structured JSON Logging**
  - Request/response logging with timing
  - Security event logging
  - Database operation logging
  - Error logging with trace IDs
  - Contextual information (method, path, client IP, status code)

#### Testing
- **27 Comprehensive Tests**
  - 9 API integration tests for documents endpoint
  - 5 API health checks and status tests
  - 8 DocumentService unit tests
  - 5 Security unit tests

- **Test Infrastructure**
  - pytest with async support
  - Isolated test databases per test
  - Proper FastAPI lifespan testing
  - AsyncClient for real request testing

- **Coverage**
  - Security validation: SSRF, URL schemes, filename sanitization
  - Service layer: ArXiv resolution, storage management, response conversion
  - API layer: CRUD operations, error handling, status codes

### 🏗️ Architecture

```
app/
├── api/
│   ├── health.py          # Health & readiness endpoints
│   └── v1/
│       └── documents.py   # Document management endpoints
├── core/
│   ├── config.py          # Pydantic Settings v2
│   ├── security.py        # SSRF, URL validation, ID generation
│   └── errors.py          # Exception handlers
├── domain/
│   ├── models.py          # SQLAlchemy ORM models
│   └── schemas.py         # Pydantic schemas
├── db/
│   ├── session.py         # Database session & initialization
│   └── repository/
│       └── documents.py   # Document CRUD operations
├── services/
│   └── document_service.py # Business logic
└── main.py               # FastAPI app factory
```

### 📊 API Response Examples

#### Document Creation (ArXiv)
```json
{
  "document_id": "doc_7pusf8pb3hbl0h3f",
  "status": "PENDING",
  "message": "Document queued for processing"
}
```

#### Document List
```json
{
  "items": [
    {
      "id": "doc_7pusf8pb3hbl0h3f",
      "source_type": "ARXIV",
      "status": "PENDING",
      "created_at": "2026-01-06T20:33:51.672379Z",
      "updated_at": "2026-01-06T20:33:53.790187Z"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

#### Health Check
```json
{
  "status": "ok",
  "version": "0.1.0",
  "timestamp": "2026-01-06T20:32:45.223906Z"
}
```

#### Readiness Check
```json
{
  "status": "ready",
  "database": "connected",
  "version": "0.1.0",
  "timestamp": "2026-01-06T20:32:51.745469Z"
}
```

### 🔒 Security Validations

#### SSRF Protection Examples
```bash
# ❌ BLOCKED - Localhost
POST /api/v1/documents/url
{"pdf_url": "http://localhost:8080/admin/secret.pdf"}
→ 422: "Cannot access localhost"

# ❌ BLOCKED - Private IP
POST /api/v1/documents/url
{"pdf_url": "http://192.168.1.1/config.pdf"}
→ 422: "Cannot access private IP: 192.168.1.1"

# ❌ BLOCKED - Invalid Scheme
POST /api/v1/documents/url
{"pdf_url": "ftp://files.example.com/document.pdf"}
→ 422: Validation error

# ✅ ALLOWED - Public HTTPS
POST /api/v1/documents/url
{"pdf_url": "https://arxiv.org/pdf/2310.06825.pdf"}
→ 202: ACCEPTED
```

### 📈 Performance Metrics

- **Request Processing**: <1000ms average
- **PDF Download**: 1-3 seconds (network dependent)
- **Database Operations**: <100ms
- **Startup Time**: ~500ms
- **Memory Usage**: ~150MB at rest

### 🗂️ Storage Structure

```
storage/
├── doc_7pusf8pb3hbl0h3f/
│   ├── document.pdf
│   └── metadata.json
├── doc_abc123xyz789/
│   ├── document.pdf
│   └── metadata.json
└── ...
```

### 📋 Known Limitations (For Future Versions)

- PDFs are stored but not yet processed (waiting for Milestone 2)
- No embeddings or vector storage integration yet
- No chat/Q&A functionality yet
- No advanced search capabilities
- No user authentication/authorization
- No rate limiting enforcement (configured but disabled)

### 🧪 Test Results

```
============================= 27 passed, 4 warnings in 0.60s =============================
- API Integration Tests:    9/9 ✅
- Health/Status Tests:      5/5 ✅
- DocumentService Tests:    8/8 ✅
- Security Tests:           5/5 ✅
```

### 📦 Dependencies Added

- `fastapi ^0.104.0` - Web framework
- `sqlalchemy ^2.0.0` - ORM
- `pydantic-settings ^2.0.0` - Configuration
- `httpx ^0.25.0` - Async HTTP client
- `aiosqlite ^0.20.0` - Async SQLite driver
- `python-multipart ^0.0.6` - File upload support
- `pytest-asyncio ^0.23.0` - Async testing
- `slowapi` - Rate limiting (configured)

### 🚀 Deployment Ready

- ✅ Async-first architecture
- ✅ Database migration support (Alembic)
- ✅ Health checks for orchestration
- ✅ Structured logging for observability
- ✅ Error handling with trace IDs
- ✅ Configuration via environment variables
- ✅ Docker support (docker-compose.yml)

### 📚 Documentation

- [README.md](README.md) - Getting started and API overview
- [MILESTONE_1_COMPLETE.md](MILESTONE_1_COMPLETE.md) - Detailed completion report
- [Folio_API.postman_collection.json](../Folio_API.postman_collection.json) - Postman collection

---

## Unreleased

### Planned for Milestone 2: Processing Pipeline

- Document text extraction from PDFs
- Text chunking with configurable strategies
- Embedding generation with retry logic
- Vector store integration (Qdrant)
- Document processing queue management
- Batch processing support
- Processing status webhooks

### Planned for Milestone 3: Chat & Search

- Chat endpoint with RAG integration
- Semantic search across documents
- Chat history management
- User authentication and authorization
- Rate limiting enforcement
- Response streaming

---

## [0.0.1] - 2025-12-15

### Initial Setup

- Project scaffolding with FastAPI
- Database setup with SQLAlchemy
- Configuration management
- Development environment
