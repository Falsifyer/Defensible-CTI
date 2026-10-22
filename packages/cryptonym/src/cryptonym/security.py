"""Security boundaries for untrusted input and external endpoints.

Cryptonym reads dossiers and talks to optional services (OpenCTI, MISP, TAXII). Every
one of those is an untrusted boundary, so the same rules apply here as anywhere else:
validate before use, fail closed, and never leak a credential or a response body into
an error message.
"""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlsplit

#: Upper bound for a single dossier, so a malformed input cannot exhaust memory.
MAX_DOSSIER_BYTES = 2 * 1024 * 1024
MAX_TEXT_CHARS = 20_000


class SecurityValidationError(ValueError):
    """Raised when untrusted input crosses a documented security boundary."""


def bounded_text(value: str | None, field: str, limit: int = MAX_TEXT_CHARS) -> str:
    """Return ``value`` bounded to ``limit`` characters, or fail closed."""
    text = value or ""
    if len(text) > limit:
        raise SecurityValidationError(f"{field} exceeds the {limit:,}-character limit")
    return text


def validate_service_url(value: str, *, allow_loopback: bool = False, allow_private: bool = False) -> str:
    """Validate an HTTP service URL and resolve its host to reduce SSRF risk.

    The host is resolved and every address is checked, but the request itself is later
    made by the SDK, which resolves again. DNS rebinding is therefore out of scope;
    pin an IP, or point the tool at a host you control, if that is in your threat model.
    """
    parsed = urlsplit((value or "").strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise SecurityValidationError("Endpoint must be an absolute HTTP(S) URL")
    if parsed.username or parsed.password or parsed.fragment:
        raise SecurityValidationError("Endpoint credentials and fragments are not allowed")
    if parsed.scheme == "http" and not (allow_loopback or allow_private):
        raise SecurityValidationError("Public endpoints must use HTTPS")
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(parsed.hostname, parsed.port)}
    except socket.gaierror as exc:
        raise SecurityValidationError("Endpoint hostname could not be resolved") from exc
    for raw_address in addresses:
        address = ipaddress.ip_address(raw_address)
        if address.is_loopback and allow_loopback:
            continue
        if address.is_private and allow_private:
            continue
        if not address.is_global:
            raise SecurityValidationError("Endpoint resolves to a disallowed network address")
    return parsed.geturl().rstrip("/")


def safe_error(prefix: str, exc: Exception) -> str:
    """A stable message that does not leak tokens, URLs or response bodies."""
    return f"{prefix}: {type(exc).__name__}"
