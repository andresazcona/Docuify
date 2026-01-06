# Docuify Backend

Backend API para aplicación tipo ChatPDF con RAG (Retrieval Augmented Generation).

**Status**: ✅ **Milestone 1 Complete** - Document Ingestion System Production Ready

## 📋 Stack Tecnológico

- **Framework**: FastAPI 0.104+
- **Python**: 3.12+
- **Database**: SQLAlchemy 2.0 (async) - SQLite (dev), PostgreSQL (prod)
- **Migraciones**: Alembic
- **Validación**: Pydantic v2
- **Logging**: JSON estructurado con structlog
- **Rate Limiting**: slowapi + Redis (configurado, deshabilitado por defecto)
- **Testing**: pytest + pytest-asyncio + httpx
- **Linting**: ruff + mypy
- **HTTP Client**: httpx (async)
- **File Storage**: Local filesystem (configurable)

## 🏗️ Estructura del Proyecto

```
backend/
├── app/
│   ├── api/
│   │   ├── health.py             # Health & readiness endpoints ✅
│   │   └── v1/
│   │       └── documents.py      # Document management (7 endpoints) ✅
│   ├── core/
│   │   ├── config.py             # Pydantic Settings v2 ✅
│   │   ├── logging.py            # Structured JSON logging ✅
│   │   ├── errors.py             # Error handling with trace IDs ✅
│   │   └── security.py           # SSRF, URL validation, ID generation ✅
│   ├── domain/
│   │   ├── models.py             # SQLAlchemy ORM models ✅
│   │   └── schemas.py            # Pydantic schemas ✅
│   ├── db/
│   │   ├── session.py            # DB session & initialization ✅
│   │   └── repository/
│   │       └── documents.py      # Document CRUD operations ✅
│   ├── services/
│   │   └── document_service.py   # Business logic (ingestion) ✅
│   └── main.py                   # FastAPI app factory ✅
├── tests/
│   ├── conftest.py               # Fixtures & configuration ✅
│   ├── api/
│   │   ├── test_documents.py     # 9 API tests ✅
│   │   └── test_health.py        # 5 health tests ✅
│   └── unit/
│       ├── test_security.py      # 5 security tests ✅
│       └── test_document_service.py  # 8 service tests ✅
├── alembic/                      # Database migrations
├── storage/                      # File storage (documents) ✅
├── pyproject.toml                # Dependencies
├── Makefile                      # Development commands
├── .env.example                  # Environment template
├── CHANGELOG.md                  # Version history ✅
├── MILESTONE_1_COMPLETE.md       # Detailed completion report
└── README.md                     # This file
```

## 🚀 Quick Start

### Requisitos

- Python 3.12+
- Poetry (gestor de dependencias)
- Git

**Nota**: PostgreSQL y Redis son opcionales (desarrollo usa SQLite por defecto)

### 1. Clonar y configurar

```bash
cd backend
poetry install
# O con make (instala deps y crea .env si falta)
make setup
```

### 2. Iniciar servidor de desarrollo

```bash
make dev
# O directamente:
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

El servidor estará disponible en: **http://localhost:8000**

### 3. Probar API

```bash
# Health check
curl http://localhost:8000/health

# Readiness check
curl http://localhost:8000/ready

# API metadata
curl http://localhost:8000/api/v1/meta
```

### 4. Usar Postman Collection

Importa la colección en Postman:
```
Docuify_API.postman_collection.json
```

Todos los endpoints están listos para probar con ejemplos incluidos.

## 🎯 Endpoints Implementados

### Health & Status (5 endpoints)

```bash
# Health check (sin dependencias)
GET /health           → 200 OK
GET /healthz          → 200 OK (kubernetes)

# Readiness check (con validación de DB)
GET /ready            → 200 OK
GET /readyz           → 200 OK (kubernetes)

# API metadata
GET /api/v1/meta      → 200 OK
```

### Document Management (7 endpoints)

```bash
# Crear documento desde ArXiv
POST /api/v1/documents/arxiv
{
  "arxiv_url": "https://arxiv.org/abs/2310.06825"
}
→ 202 ACCEPTED

# Crear documento desde URL pública
POST /api/v1/documents/url
{
  "pdf_url": "https://arxiv.org/pdf/2310.06825.pdf"
}
→ 202 ACCEPTED

# Subir archivo PDF
POST /api/v1/documents/upload
Content-Type: multipart/form-data
file: <archivo.pdf>
→ 202 ACCEPTED

# Listar documentos
GET /api/v1/documents?skip=0&limit=20
→ 200 OK

# Obtener documento por ID
GET /api/v1/documents/{document_id}
→ 200 OK

# Reintentar documento fallido
POST /api/v1/documents/{document_id}/retry
→ 202 ACCEPTED (si status=FAILED)
→ 409 CONFLICT (si status≠FAILED)

# Eliminar documento
DELETE /api/v1/documents/{document_id}
→ 204 NO CONTENT
```

## 🔒 Características de Seguridad

### SSRF Protection ✅

Bloquea intentos de acceso a:
- Localhost (127.0.0.1)
- IPs privadas (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
- Link-local (169.254.0.0/16)
- Multicast (224.0.0.0/4)

**Ejemplo**:
```bash
# ❌ BLOQUEADO
curl -X POST http://localhost:8000/api/v1/documents/url \
  -H "Content-Type: application/json" \
  -d '{"pdf_url": "http://localhost:8080/secret.pdf"}'
→ 422 UNPROCESSABLE ENTITY
"URL validation failed: Cannot access localhost"
```

### URL Scheme Validation ✅

- Solo permite: `https://`, `http://`
- Rechaza: `ftp://`, `file://`, etc.

### PDF Validation ✅

- Valida magic bytes (%PDF)
- Valida Content-Type
- Enforces file size limits

### Secure ID Generation ✅

- IDs criptográficamente seguros
- Formato: `doc_<16-caracteres-aleatorios>`

## 📊 API Responses

### Crear documento exitoso

```json
{
  "document_id": "doc_7pusf8pb3hbl0h3f",
  "status": "PENDING",
  "message": "Document queued for processing"
}
```

### Listar documentos

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

### Health check

```json
{
  "status": "ok",
  "version": "0.1.0",
  "timestamp": "2026-01-06T20:32:45.223906Z"
}
```

### Error response

```json
{
  "code": "VALIDATION_ERROR",
  "message": "URL validation failed: Cannot access private IP: 192.168.1.1",
  "trace_id": "c64ba204-05c0-40c9-b051-86ff153e465f",
  "path": "/api/v1/documents/url",
  "method": "POST",
  "status_code": 422
}
```

## 🧪 Testing

### Ejecutar all tests

```bash
make test
# o:
poetry run pytest tests/ -v
```

### Tests with coverage

```bash
make test-cov
# Genera reporte en htmlcov/
```

### Test specific file

```bash
poetry run pytest tests/api/test_documents.py -v
```

### Test results (27 tests passing)

```
tests/api/test_documents.py ............... [9/27]
tests/api/test_health.py .................. [5/27]
tests/unit/test_document_service.py ....... [8/27]
tests/unit/test_security.py ............... [5/27]

======================== 27 passed in 0.60s ========================
```

## 🔧 Makefile Commands

```bash
# Setup
make setup           # Instala deps y crea .env si falta
make install         # Instalar dependencias
make env             # Crear .env

# Development
make up              # Alias de docker-up
make down            # Alias de docker-down
make dev             # Iniciar servidor con reload
make docker-up       # Iniciar PostgreSQL, Redis, Qdrant
make docker-down     # Detener servicios

# Testing & Quality
make test            # Ejecutar tests
make test-cov        # Tests con coverage
make lint            # Verificar código con ruff
make format          # Formatear código
make type-check      # Type checking con mypy
make check           # Ejecutar todo (lint + type + test)

# Database
make migrate         # Crear nueva migración
make db-upgrade      # Aplicar migraciones
make db-downgrade    # Revertir última migración

# Cleanup
make clean           # Limpiar cache y archivos temporales
```

## 📦 Storage

Los documentos se almacenan en:

```
storage/
├── doc_7pusf8pb3hbl0h3f/
│   ├── document.pdf        # Archivo PDF descargado
│   └── metadata.json       # Metadatos (opcional)
└── ...
```

## 🔄 Variables de Entorno (Development)

Por defecto, la app funciona con valores seguros:

```bash
# Database (default: SQLite)
DATABASE_URL=sqlite+aiosqlite:///./dev.db

# Security
SECRET_KEY=dev-secret-key-change-me-please-32chars

# Storage
STORAGE_DIR=./storage

# Rate Limiting (disabled by default)
RATE_LIMIT_ENABLED=false

# Environment
ENVIRONMENT=development
API_VERSION=0.1.0
```

**Para producción**: Editar `.env` con valores reales y usar PostgreSQL

## 📝 Logging

Todos los eventos se registran en JSON estructurado:

```json
{
  "method": "POST",
  "path": "/api/v1/documents/url",
  "status_code": 202,
  "event": "request_completed",
  "client": "127.0.0.1",
  "timestamp": "2026-01-06T20:37:56.412711Z",
  "trace_id": "..." 
}
```

Los logs son útiles para debugging, monitoreo y auditoría.

## 🗂️ Configuración de Variables de Entorno

```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

**Variables críticas a configurar:**

```bash
# Producción: PostgreSQL
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/docuify

REDIS_URL=redis://localhost:6379/0
SECRET_KEY=<genera-una-clave-segura-de-al-menos-32-caracteres>
LLM_API_KEY=<tu-api-key-de-gemini-o-openai>
EMBEDDING_API_KEY=<tu-api-key-para-embeddings>
```

## 📚 Documentación Adicional

- [CHANGELOG.md](CHANGELOG.md) - Historial de cambios y versiones
- [MILESTONE_1_COMPLETE.md](MILESTONE_1_COMPLETE.md) - Reporte detallado de Milestone 1
- [Postman Collection](../Docuify_API.postman_collection.json) - Tests de API listos para usar

## 🎯 Roadmap del Proyecto

### ✅ **Milestone 1: Document Ingestion** (COMPLETADO)

- ✅ DocumentService con 3 métodos de ingestión
- ✅ ArXiv PDF downloads con resolución automática
- ✅ URL downloads con SSRF protection
- ✅ File upload con PDF validation
- ✅ Storage management
- ✅ 7 endpoints completos
- ✅ 27 tests (100% passing)
- ✅ Security hardening

### 📋 **Milestone 2: Processing Pipeline** (PRÓXIMO)

- ⏳ Text extraction from PDFs (PDF2Markdown)
- ⏳ Content cleaning y normalization
- ⏳ Chunking with overlap strategies
- ⏳ Status tracking (DOWNLOADING → PROCESSING → READY)
- ⏳ Worker queue (async processing)
- ⏳ Error retry logic
- ⏳ Batch processing support

### 📊 **Milestone 3: RAG Integration** (FUTURO)

- ⏳ Embedding generation
- ⏳ Vector store integration (Qdrant)
- ⏳ Semantic search
- ⏳ Retrieval with ranking
- ⏳ Citation system

### 💬 **Milestone 4: Chat & Search** (FUTURO)

- ⏳ Chat endpoint `/api/v1/chat`
- ⏳ LLM integration (Gemini/OpenAI)
- ⏳ RAG prompt engineering
- ⏳ Chat history management
- ⏳ Response streaming (SSE)
- ⏳ Conversation search

### 🔐 **Milestone 5: Production Hardening** (FUTURO)

- ⏳ JWT Authentication
- ⏳ Role-based Authorization
- ⏳ Multi-user support
- ⏳ Prometheus metrics
- ⏳ Complete Docker setup
- ⏳ CI/CD pipeline

## 🏢 Arquitectura de Producción

### Planned Services

```
┌─────────────────┐
│   FastAPI App   │
│  (8 replicas)   │
└────────┬────────┘
         │
    ┌────┴────┐
    │   Load   │
    │ Balancer │
    │ (Nginx)  │
    └────┬────┘
         │
    ┌────┴─────────────┬──────────────┐
    │                  │              │
┌───┴────┐  ┌─────────┴────┐  ┌──────┴──────┐
│PostgreSQL│  │    Redis    │  │   Qdrant    │
│   (HA)   │  │   (Cache)   │  │  (Vectors)  │
└──────────┘  └─────────────┘  └─────────────┘

Worker Queue: ArQ / Celery
Monitoring: Prometheus + Grafana
Logs: ELK Stack / DataDog
```

## 🤝 Contribuir

1. Crear rama feature: `git checkout -b feature/nombre`
2. Commit cambios: `git commit -am 'Add feature'`
3. Push a la rama: `git push origin feature/nombre`
4. Crear Pull Request

## 📧 Contacto

Para preguntas o sugerencias sobre el backend, contacta al equipo de desarrollo.

## 📄 Licencia

Este proyecto está bajo licencia MIT.

