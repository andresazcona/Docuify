"""Security utilities for SSRF protection and validation."""

import ipaddress
import re
from typing import Final
from urllib.parse import urlparse

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Private IP ranges to block for SSRF protection
PRIVATE_IP_RANGES: Final[list[ipaddress.IPv4Network | ipaddress.IPv6Network]] = [
    # IPv4 private ranges
    ipaddress.IPv4Network("0.0.0.0/8"),  # Current network
    ipaddress.IPv4Network("10.0.0.0/8"),  # Private network
    ipaddress.IPv4Network("127.0.0.0/8"),  # Loopback
    ipaddress.IPv4Network("169.254.0.0/16"),  # Link-local
    ipaddress.IPv4Network("172.16.0.0/12"),  # Private network
    ipaddress.IPv4Network("192.168.0.0/16"),  # Private network
    ipaddress.IPv4Network("224.0.0.0/4"),  # Multicast
    ipaddress.IPv4Network("240.0.0.0/4"),  # Reserved
    # IPv6 ranges
    ipaddress.IPv6Network("::1/128"),  # Loopback
    ipaddress.IPv6Network("fe80::/10"),  # Link-local
    ipaddress.IPv6Network("fc00::/7"),  # Unique local
]


class SecurityError(Exception):
    """Base exception for security-related errors."""

    pass


class SSRFError(SecurityError):
    """Exception raised when SSRF attack is detected."""

    pass


class InvalidURLError(SecurityError):
    """Exception raised when URL validation fails."""

    pass


def is_private_ip(ip_str: str) -> bool:
    """
    Check if an IP address is private/internal.

    Args:
        ip_str: IP address string to check

    Returns:
        True if IP is private/internal, False otherwise
    """
    try:
        ip = ipaddress.ip_address(ip_str)
        return any(ip in network for network in PRIVATE_IP_RANGES)
    except ValueError:
        logger.warning("invalid_ip_address", ip=ip_str)
        return True  # Treat invalid IPs as private (fail-safe)


def validate_url_scheme(url: str) -> None:
    """
    Validate that URL uses an allowed scheme.

    Args:
        url: URL to validate

    Raises:
        InvalidURLError: If scheme is not allowed
    """
    settings = get_settings()
    parsed = urlparse(url)

    if not parsed.scheme:
        raise InvalidURLError("URL must have a scheme")

    if parsed.scheme.lower() not in settings.allowed_schemes_list:
        raise InvalidURLError(
            f"Scheme '{parsed.scheme}' not allowed. "
            f"Allowed: {', '.join(settings.allowed_schemes_list)}"
        )


def validate_url_host(url: str) -> None:
    """
    Validate URL host to prevent SSRF attacks.

    Args:
        url: URL to validate

    Raises:
        SSRFError: If host points to private/internal network
        InvalidURLError: If host is invalid
    """
    parsed = urlparse(url)

    if not parsed.hostname:
        raise InvalidURLError("URL must have a valid hostname")

    hostname = parsed.hostname.lower()

    # Check for localhost aliases
    if hostname in ("localhost", "0.0.0.0"):
        raise SSRFError("Cannot access localhost")

    # Check for IP addresses
    if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", hostname):
        if is_private_ip(hostname):
            raise SSRFError(f"Cannot access private IP: {hostname}")

    # Check for IPv6 addresses
    if ":" in hostname:
        ip_match = re.search(r"\[([^\]]+)\]", hostname)
        if ip_match:
            ipv6_addr = ip_match.group(1)
            if is_private_ip(ipv6_addr):
                raise SSRFError(f"Cannot access private IPv6: {ipv6_addr}")


def validate_url_for_download(url: str) -> None:
    """
    Comprehensive URL validation for safe downloading.

    Args:
        url: URL to validate

    Raises:
        InvalidURLError: If URL format is invalid
        SSRFError: If URL poses SSRF risk
    """
    logger.info("validating_download_url", url=url)

    # Basic format check
    if not url or not url.strip():
        raise InvalidURLError("URL cannot be empty")

    # Scheme validation
    validate_url_scheme(url)

    # Host validation (SSRF protection)
    validate_url_host(url)

    logger.info("url_validation_passed", url=url)


def generate_secure_id(prefix: str) -> str:
    """
    Generate a secure random ID with prefix.

    Args:
        prefix: Prefix for the ID (e.g., "doc", "chat")

    Returns:
        Formatted ID string (e.g., "doc_abc123xyz")
    """
    import secrets
    import string

    alphabet = string.ascii_lowercase + string.digits
    random_part = "".join(secrets.choice(alphabet) for _ in range(16))
    return f"{prefix}_{random_part}"


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize a filename to prevent directory traversal and other attacks.

    Args:
        filename: Original filename
        max_length: Maximum allowed length

    Returns:
        Sanitized filename safe for filesystem use
    """
    # Remove path components
    filename = filename.split("/")[-1].split("\\")[-1]

    # Remove potentially dangerous characters
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", filename)

    # Remove leading/trailing dots and spaces
    filename = filename.strip(". ")

    # Ensure not empty
    if not filename:
        filename = "unnamed_file"

    # Truncate if too long
    if len(filename) > max_length:
        name_part, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
        max_name_length = max_length - len(ext) - 1 if ext else max_length
        filename = name_part[:max_name_length] + ("." + ext if ext else "")

    return filename
