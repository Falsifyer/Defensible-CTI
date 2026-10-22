"""Tests for the network fetch boundary."""

from __future__ import annotations

import json

import pytest

from cryptonym.ingest.fetch import MAX_FETCH_BYTES, attack_stix_url, fetch_json
from cryptonym.security import SecurityValidationError


def test_fetch_json_parses_with_injected_fetcher() -> None:
    data = fetch_json("https://example.com/x.json", fetcher=lambda url: json.dumps({"a": 1}))
    assert data == {"a": 1}


def test_fetch_json_rejects_non_json() -> None:
    with pytest.raises(SecurityValidationError, match="JSON"):
        fetch_json("https://example.com/x", fetcher=lambda url: "<html>not json</html>")


def test_fetch_json_rejects_plain_http() -> None:
    with pytest.raises(SecurityValidationError):
        fetch_json("http://example.com", fetcher=lambda url: "{}")


def test_fetch_json_enforces_size_cap() -> None:
    with pytest.raises(SecurityValidationError, match="size"):
        fetch_json("https://example.com", fetcher=lambda url: "x" * (MAX_FETCH_BYTES + 1))


def test_attack_stix_url_builds_a_domain_endpoint() -> None:
    url = attack_stix_url("mobile-attack")
    assert url.startswith("https://")
    assert url.endswith("/mobile-attack/mobile-attack.json")
