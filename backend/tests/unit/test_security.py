"""Tests for security utilities."""
import pytest

from app.core.security import (
    InvalidURLError,
    SSRFError,
    generate_secure_id,
    is_private_ip,
    sanitize_filename,
    validate_url_for_download,
)


def test_is_private_ip() -> None:
    """Test private IP detection."""
    assert is_private_ip("127.0.0.1") is True
    assert is_private_ip("192.168.1.1") is True
    assert is_private_ip("10.0.0.1") is True
    assert is_private_ip("172.16.0.1") is True
    assert is_private_ip("8.8.8.8") is False
    assert is_private_ip("1.1.1.1") is False


def test_validate_url_scheme() -> None:
    """Test URL scheme validation."""
    # Valid schemes
    validate_url_for_download("http://example.com/file.pdf")
    validate_url_for_download("https://example.com/file.pdf")

    # Invalid schemes
    with pytest.raises(InvalidURLError):
        validate_url_for_download("ftp://example.com/file.pdf")

    with pytest.raises(InvalidURLError):
        validate_url_for_download("file:///etc/passwd")


def test_validate_url_ssrf_protection() -> None:
    """Test SSRF protection."""
    # Valid public URLs
    validate_url_for_download("https://example.com/file.pdf")

    # SSRF attempts
    with pytest.raises(SSRFError):
        validate_url_for_download("http://localhost/file.pdf")

    with pytest.raises(SSRFError):
        validate_url_for_download("http://127.0.0.1/file.pdf")

    with pytest.raises(SSRFError):
        validate_url_for_download("http://192.168.1.1/file.pdf")


def test_generate_secure_id() -> None:
    """Test secure ID generation."""
    doc_id = generate_secure_id("doc")
    assert doc_id.startswith("doc_")
    assert len(doc_id) > 10

    chat_id = generate_secure_id("chat")
    assert chat_id.startswith("chat_")

    # IDs should be unique
    assert generate_secure_id("doc") != generate_secure_id("doc")


def test_sanitize_filename() -> None:
    """Test filename sanitization."""
    assert sanitize_filename("document.pdf") == "document.pdf"
    assert sanitize_filename("../../../etc/passwd") == "passwd"
    assert sanitize_filename("file<>name.pdf") == "filename.pdf"
    assert sanitize_filename("file:name.pdf") == "filename.pdf"
    assert sanitize_filename("   .hidden   ") == "hidden"
    assert sanitize_filename("") == "unnamed_file"
