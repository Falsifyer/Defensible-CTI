"""Fetch source documents over the network, safely.

Network access is deliberately **not** in the core: this module validates the endpoint
(SSRF-aware), enforces a size cap, and accepts JSON only. The actual request is
delegated to an injected fetcher, so parsing and ingest stay offline and testable.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from cryptonym.security import SecurityValidationError, validate_service_url

MAX_FETCH_BYTES = 10 * 1024 * 1024

#: Canonical public endpoint for the ATT&CK STIX corpus.
ATTACK_STIX_URL = "https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/{domain}/{domain}.json"


def attack_stix_url(domain: str = "enterprise-attack") -> str:
    """Return the public STIX URL for an ATT&CK domain."""
    return ATTACK_STIX_URL.format(domain=domain)


def fetch_json(url: str, *, fetcher: Callable[[str], str] | None = None, allow_private: bool = False) -> Any:
    """Fetch and parse a JSON document from a validated endpoint.

    Only JSON is accepted, and only up to a size cap; a non-JSON response is a failure,
    not something to be guessed at.
    """
    endpoint = validate_service_url(url, allow_private=allow_private)
    payload = (fetcher or _default_fetcher)(endpoint)
    if len(payload.encode("utf-8")) > MAX_FETCH_BYTES:
        raise SecurityValidationError("source response exceeds the size limit")
    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        raise SecurityValidationError("source did not return valid JSON") from exc


def _default_fetcher(url: str, timeout: int = 15) -> str:  # pragma: no cover - network only
    import urllib.request

    request = urllib.request.Request(url, headers={"User-Agent": "cryptonym", "Accept": "application/json"})  # noqa: S310
    response = urllib.request.urlopen(request, timeout=timeout)  # noqa: S310  # nosec B310
    with response:
        return response.read().decode("utf-8", "replace")
