"""Document service implementing ingestion flows."""
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import aiofiles
import httpx

from app.core import (
    ConflictError,
    NotFoundError,
    ServiceUnavailableError,
    ValidationError,
    generate_secure_id,
    get_logger,
    get_settings,
    sanitize_filename,
    validate_url_for_download,
)
from app.db.models import Document
from app.domain import (
    DocumentCreateResponse,
    DocumentListResponse,
    DocumentMetadata,
    DocumentResponse,
    DocumentStatus,
    DocumentCreateArxivRequest,
    DocumentCreateUrlRequest,
    SourceType,
)
from app.repositories import DocumentRepository


class DocumentService:
    """Business logic for document ingestion and management."""

    def __init__(self, repository: DocumentRepository | None = None):
        self.settings = get_settings()
        self.repository = repository or DocumentRepository()
        self.logger = get_logger(self.__class__.__name__)

    # ---------------------- Public API ----------------------
    async def create_from_arxiv(self, request: DocumentCreateArxivRequest, session) -> DocumentCreateResponse:
        """Ingest a document from an arXiv URL."""
        try:
            pdf_url, arxiv_id = self._resolve_arxiv_pdf_url(str(request.arxiv_url))
        except Exception as exc:
            raise ValidationError(f"Invalid arXiv URL: {exc}") from exc

        document_id = generate_secure_id("doc")
        filename = sanitize_filename(f"{arxiv_id or document_id}.pdf")
        storage_path = self._build_storage_path(document_id, filename)

        document = Document(
            id=document_id,
            source_type=SourceType.ARXIV,
            source_ref=str(request.arxiv_url),
            original_filename=filename,
            status=DocumentStatus.DOWNLOADING,
            storage_path=str(storage_path),
            meta_json={"arxiv_id": arxiv_id} if arxiv_id else None,
        )

        document = await self.repository.create(session, document)

        try:
            await self._download_pdf(pdf_url, storage_path)
            document = await self.repository.update_fields(
                session,
                document_id=document.id,
                status=DocumentStatus.READY,
                error_message=None,
            )
        except (ValidationError, ServiceUnavailableError):
            raise
        except Exception as exc:  # pragma: no cover - logged and re-raised
            await self._mark_failed(session, document.id, str(exc))
            raise ServiceUnavailableError("Failed to download arXiv PDF") from exc

        return DocumentCreateResponse(document_id=document.id, status=document.status)

    async def create_from_url(self, request: DocumentCreateUrlRequest, session) -> DocumentCreateResponse:
        """Ingest a document from a public PDF URL with SSRF guard."""
        try:
            validate_url_for_download(str(request.pdf_url))
        except Exception as exc:
            raise ValidationError(f"URL validation failed: {exc}") from exc

        document_id = generate_secure_id("doc")
        filename = sanitize_filename(f"{document_id}.pdf")
        storage_path = self._build_storage_path(document_id, filename)

        document = Document(
            id=document_id,
            source_type=SourceType.URL,
            source_ref=str(request.pdf_url),
            original_filename=filename,
            status=DocumentStatus.DOWNLOADING,
            storage_path=str(storage_path),
        )
        document = await self.repository.create(session, document)

        try:
            await self._download_pdf(str(request.pdf_url), storage_path)
            document = await self.repository.update_fields(
                session,
                document_id=document.id,
                status=DocumentStatus.READY,
                error_message=None,
            )
        except (ValidationError, ServiceUnavailableError):
            raise
        except Exception as exc:  # pragma: no cover - logged and re-raised
            await self._mark_failed(session, document.id, str(exc))
            raise ServiceUnavailableError("Failed to download PDF") from exc

        return DocumentCreateResponse(document_id=document.id, status=document.status)

    async def create_from_upload(self, upload_file, session) -> DocumentCreateResponse:
        """Ingest a document from an uploaded PDF file."""
        filename = sanitize_filename(upload_file.filename or "uploaded.pdf")
        document_id = generate_secure_id("doc")
        storage_path = self._build_storage_path(document_id, filename)

        document = Document(
            id=document_id,
            source_type=SourceType.UPLOAD,
            source_ref=filename,
            original_filename=filename,
            status=DocumentStatus.UPLOADED,
            storage_path=str(storage_path),
        )
        document = await self.repository.create(session, document)

        try:
            await self._write_upload(upload_file, storage_path)
            document = await self.repository.update_fields(
                session,
                document_id=document.id,
                status=DocumentStatus.READY,
                error_message=None,
            )
        except (ValidationError, ServiceUnavailableError):
            raise
        except Exception as exc:  # pragma: no cover - logged and re-raised
            await self._mark_failed(session, document.id, str(exc))
            raise ServiceUnavailableError("Failed to store uploaded PDF") from exc

        return DocumentCreateResponse(document_id=document.id, status=document.status)

    async def list_documents(self, session, *, limit: int, offset: int) -> DocumentListResponse:
        documents, total = await self.repository.list(session, limit=limit, offset=offset)
        return DocumentListResponse(
            documents=[self._to_response_model(doc) for doc in documents],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def get_document(self, session, document_id: str) -> DocumentResponse:
        document = await self.repository.get(session, document_id)
        return self._to_response_model(document)

    async def retry_document(self, session, document_id: str) -> DocumentCreateResponse:
        document = await self.repository.get(session, document_id)
        if document.status not in {DocumentStatus.FAILED}:
            raise ConflictError("Document is not in a retryable (FAILED) state")

        document = await self.repository.update_fields(
            session,
            document_id=document.id,
            status=DocumentStatus.PROCESSING,
            error_message=None,
        )
        return DocumentCreateResponse(document_id=document.id, status=document.status)

    async def delete_document(self, session, document_id: str) -> None:
        document = await self.repository.get(session, document_id)
        await self.repository.delete(session, document_id)
        self._delete_storage(document.storage_path)

    # ---------------------- Helpers ----------------------
    async def _download_pdf(self, url: str, dest_path: Path) -> None:
        """Download a PDF with limits and validation."""
        self._ensure_dir(dest_path.parent)
        timeout = httpx.Timeout(self.settings.download_timeout_secs)

        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            async with client.stream("GET", url) as response:
                if response.status_code >= 400:
                    raise ServiceUnavailableError(
                        f"Failed to download file. Status code: {response.status_code}"
                    )

                content_type = response.headers.get("content-type", "")
                total = 0
                first_chunk: bytes | None = None

                async with aiofiles.open(dest_path, "wb") as file:
                    async for chunk in response.aiter_bytes():
                        if not chunk:
                            continue
                        if first_chunk is None:
                            first_chunk = chunk
                            self._validate_pdf_chunk(first_chunk, content_type)
                        total += len(chunk)
                        if total > self.settings.max_download_bytes:
                            raise ValidationError("Downloaded file exceeds max size")
                        await file.write(chunk)

                if first_chunk is None:
                    raise ValidationError("Empty file received")

    async def _write_upload(self, upload_file, dest_path: Path) -> None:
        """Persist uploaded file enforcing size and PDF validation."""
        self._ensure_dir(dest_path.parent)
        content_type = upload_file.content_type or ""
        total = 0
        first_chunk: bytes | None = None

        async with aiofiles.open(dest_path, "wb") as out:
            while True:
                chunk = await upload_file.read(self.settings.max_upload_bytes)
                if not chunk:
                    break
                if first_chunk is None:
                    first_chunk = chunk
                    self._validate_pdf_chunk(first_chunk, content_type)
                total += len(chunk)
                if total > self.settings.max_upload_bytes:
                    raise ValidationError("Uploaded file exceeds max size")
                await out.write(chunk)

        if first_chunk is None:
            raise ValidationError("Uploaded file is empty")

    def _validate_pdf_chunk(self, chunk: bytes, content_type: str) -> None:
        """Validate that the first bytes likely correspond to a PDF file."""
        if "application/pdf" in content_type.lower():
            return
        if chunk.startswith(b"%PDF"):
            return
        # Some PDFs have a few bytes then %PDF; search in first KB
        if b"%PDF" in chunk[:1024]:
            return
        raise ValidationError("File is not a valid PDF")

    def _build_storage_path(self, document_id: str, filename: str) -> Path:
        base = Path(self.settings.storage_dir)
        return base / document_id / filename

    def _ensure_dir(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)

    def _delete_storage(self, storage_path: str | None) -> None:
        if not storage_path:
            return
        path = Path(storage_path)
        if path.exists():
            try:
                path.unlink()
                # Remove parent dir if empty
                parent = path.parent
                if parent.is_dir() and not any(parent.iterdir()):
                    parent.rmdir()
            except Exception:  # pragma: no cover - defensive cleanup
                self.logger.warning("failed_to_remove_storage", storage_path=storage_path)

    async def _mark_failed(self, session, document_id: str, message: str) -> None:
        await self.repository.update_fields(
            session,
            document_id=document_id,
            status=DocumentStatus.FAILED,
            error_message=message,
        )

    def _resolve_arxiv_pdf_url(self, url: str) -> tuple[str, str | None]:
        parsed = urlparse(url)
        parts = parsed.path.strip("/").split("/")
        arxiv_id: str | None = None

        if len(parts) >= 2 and parts[0] == "abs":
            arxiv_id = parts[1]
            return f"https://arxiv.org/pdf/{arxiv_id}.pdf", arxiv_id
        if len(parts) >= 2 and parts[0] == "pdf":
            # path like pdf/XXXX.pdf
            arxiv_id = parts[1].replace(".pdf", "")
            return url, arxiv_id

        # Fallback: use original URL
        return url, arxiv_id

    def _to_response_model(self, document: Document) -> DocumentResponse:
        metadata = None
        if document.meta_json:
            metadata = DocumentMetadata(**document.meta_json)

        return DocumentResponse(
            id=document.id,
            source_type=document.source_type,
            source_ref=document.source_ref,
            original_filename=document.original_filename,
            status=document.status,
            error_message=document.error_message,
            metadata=metadata,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )
