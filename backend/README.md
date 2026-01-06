# Docuify Backend

Backend API para aplicación tipo ChatPDF con RAG (Retrieval Augmented Generation).

## Stack Tecnológico

- **Framework**: FastAPI
- **Python**: 3.11+
- **Database**: PostgreSQL con SQLAlchemy 2.0 (async)
- **Migraciones**: Alembic
- **Validación**: Pydantic v2
- **Logging**: structlog (JSON estructurado)
- **Rate Limiting**: slowapi + Redis
- **Testing**: pytest + httpx
- **Linting**: ruff + mypy

## Estructura del Proyecto

```
backend/
├── app/
│   ├── api/              # API endpoints
│   │   ├── health.py     # Health checks
│   │   └── v1/           # API v1
│   │       ├── meta.py
│   │       ├── documents.py
│   │       └── chat.py
│   ├── core/             # Core utilities
│   │   ├── config.py     # Settings
│   │   ├── logging.py    # Logging config
│   │   ├── errors.py     # Error handling
│   │   └── security.py   # Security utilities
│   ├── domain/           # Domain models/schemas
│   │   └── schemas.py    # Pydantic schemas
│   ├── db/               # Database layer
│   │   ├── session.py    # DB session management
│   │   └── models.py     # SQLAlchemy models
│   ├── services/         # Business logic (placeholder)
│   ├── repositories/     # Data access (placeholder)
│   ├── workers/          # Background jobs (placeholder)
│   └── main.py           # Application factory
├── tests/                # Test suite
│   ├── api/              # API tests
│   └── unit/             # Unit tests
├── alembic/              # Database migrations
├── storage/              # File storage
├── pyproject.toml        # Dependencies
├── .env.example          # Environment template
└── README.md             # This file
```

## Instalación y Configuración

### Prerequisitos

- Python 3.11+
- PostgreSQL 14+
- Redis 6+
- Poetry (gestor de dependencias)

### 1. Clonar y configurar entorno

```bash
cd backend
```

### 2. Instalar Poetry (si no lo tienes)

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

### 3. Instalar dependencias

```bash
poetry install
```

### 4. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

**Variables críticas a configurar:**

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/docuify
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=<genera-una-clave-segura-de-al-menos-32-caracteres>
LLM_API_KEY=<tu-api-key-de-gemini-o-openai>
EMBEDDING_API_KEY=<tu-api-key-para-embeddings>
```

### 5. Crear base de datos

```bash
# En PostgreSQL
createdb docuify
```

### 6. Ejecutar migraciones

```bash
poetry run alembic upgrade head
```

## Ejecutar Aplicación

### Modo desarrollo (con reload)

```bash
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

O simplemente:

```bash
poetry run uvicorn app.main:app --reload
```

### Acceder a la documentación

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/healthz

## Testing

### Ejecutar todos los tests

```bash
poetry run pytest
```

### Con cobertura

```bash
poetry run pytest --cov=app --cov-report=html
```

### Tests específicos

```bash
poetry run pytest tests/api/test_health.py -v
```

## Linting y Formateo

### Ejecutar ruff (linting + formatting)

```bash
poetry run ruff check app/ tests/
poetry run ruff format app/ tests/
```

### Ejecutar mypy (type checking)

```bash
poetry run mypy app/
```

### Pre-commit hooks (opcional)

```bash
poetry run pre-commit install
poetry run pre-commit run --all-files
```

## Base de Datos

### Crear nueva migración

```bash
poetry run alembic revision --autogenerate -m "Descripción del cambio"
```

### Aplicar migraciones

```bash
poetry run alembic upgrade head
```

### Revertir migración

```bash
poetry run alembic downgrade -1
```

## Seguridad

El backend implementa las siguientes medidas de seguridad desde el inicio:

- **CORS** configurado con allowlist de orígenes
- **Rate Limiting** en endpoints sensibles (Redis-backed)
- **SSRF Protection** para descarga de URLs
- **Input Validation** con Pydantic v2
- **Manejo de errores** sin exponer información sensible
- **Sanitización** de nombres de archivos
- **Trace IDs** para tracking de errores

## API Endpoints

### Health & Meta

- `GET /healthz` - Health check básico
- `GET /readyz` - Readiness check (valida DB)
- `GET /api/v1/meta` - Metadata y configuración

### Documents (Placeholder)

- `POST /api/v1/documents/arxiv` - Crear desde arXiv
- `POST /api/v1/documents/url` - Crear desde URL
- `POST /api/v1/documents/upload` - Upload PDF
- `GET /api/v1/documents` - Listar documentos
- `GET /api/v1/documents/{id}` - Obtener documento
- `POST /api/v1/documents/{id}/retry` - Reintentar procesamiento
- `DELETE /api/v1/documents/{id}` - Eliminar documento

### Chat (Placeholder)

- `POST /api/v1/chats` - Crear chat
- `GET /api/v1/chats/{id}` - Obtener chat
- `POST /api/v1/chat` - Enviar mensaje
- `POST /api/v1/chat/stream` - Mensaje con streaming

**Nota**: Los endpoints marcados como "Placeholder" retornan 501/503 hasta que se implemente su lógica.

## Próximos Pasos

Este es el **esqueleto base** del backend. Los siguientes pasos de desarrollo son:

1. **M1: Ingestión**
   - Implementar descarga desde arXiv
   - Implementar descarga desde URL pública
   - Implementar upload de archivos
   - Almacenamiento en filesystem/S3

2. **M2: Procesamiento**
   - Integrar MarkItDown para conversión PDF→Markdown
   - Implementar limpieza de contenido
   - Implementar chunking con overlap
   - Workers asíncronos (Celery/RQ/ARQ)

3. **M3: RAG**
   - Integrar vector store (Qdrant/Chroma)
   - Implementar embeddings
   - Implementar retrieval
   - Scoring y ranking

4. **M4: Chat**
   - Integrar LLM (Gemini/OpenAI)
   - Implementar generación con contexto
   - Sistema de citas con locators
   - Opcional: streaming con SSE

5. **M5: Hardening**
   - Autenticación (JWT)
   - Multiusuario
   - Monitoreo y métricas
   - Docker Compose completo

## Docker (Futuro)

Se incluirá un `docker-compose.yml` completo con:
- Backend (FastAPI)
- PostgreSQL
- Redis
- Qdrant (vector DB)
- Workers

## Recursos

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/)
- [Pydantic v2](https://docs.pydantic.dev/latest/)
- [Alembic](https://alembic.sqlalchemy.org/)


