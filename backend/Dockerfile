# syntax=docker/dockerfile:1
# Stage 1: install the app and its dependencies into /install, and fetch the embedding model.
FROM python:3.12-slim AS build
ARG EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1 FASTEMBED_CACHE_PATH=/models
WORKDIR /src
COPY pyproject.toml README.md ./
COPY app ./app
RUN pip install --prefix=/install ".[embeddings]"
# Bake the model into the image so the first upload does not download 200 MB at runtime.
RUN PYTHONPATH=/install/lib/python3.12/site-packages python -c \
    "from fastembed import TextEmbedding; TextEmbedding(model_name='${EMBEDDING_MODEL}')"

# Stage 2: small runtime image, non-root.
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 \
    FASTEMBED_CACHE_PATH=/models \
    EMBEDDING_PROVIDER=fastembed \
    STORAGE_DIR=/data/storage \
    ENVIRONMENT=production \
    RELOAD=false
COPY --from=build /install /usr/local
COPY --from=build /models /models
RUN useradd --system --uid 10001 --create-home folio \
    && mkdir -p /data/storage \
    && chown -R folio /data /models
USER folio
WORKDIR /home/folio
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --start-period=20s --retries=5 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health', timeout=2).status == 200 else 1)"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
