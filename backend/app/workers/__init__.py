"""Workers module - Background job processing.

This module will contain worker implementations for asynchronous tasks
such as document processing, chunking, indexing, and RAG operations.

Technologies to consider:
- Celery with Redis broker
- RQ (Redis Queue)
- ARQ (async Redis queue)
"""

# Future workers will be implemented here:
# - DocumentProcessingWorker: Convert PDF to text/markdown
# - ChunkingWorker: Split documents into chunks
# - IndexingWorker: Generate embeddings and index chunks
# - CleanupWorker: Handle document deletion and cleanup
