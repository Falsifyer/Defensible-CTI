"""Tests for source snapshots."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from cryptonym.security import SecurityValidationError
from cryptonym.snapshot import MAX_SNAPSHOT_BYTES, Snapshot, fetch, load, write


def test_capture_records_a_stable_hash() -> None:
    snapshot = Snapshot.capture("https://example.com", "hello", captured_at="2026-10-09T00:00:00Z")
    assert snapshot.verify()
    assert snapshot.sha256 == hashlib.sha256(b"hello").hexdigest()


def test_verify_detects_tampering() -> None:
    original = Snapshot.capture("https://example.com", "hello")
    tampered = Snapshot(
        source=original.source,
        sha256=original.sha256,
        captured_at=original.captured_at,
        content="evil",
    )
    assert tampered.verify() is False


def test_capture_rejects_oversized_content() -> None:
    with pytest.raises(SecurityValidationError, match="exceeds"):
        Snapshot.capture("https://example.com", "a" * (MAX_SNAPSHOT_BYTES + 1))


def test_fetch_validates_endpoint_and_delegates_to_injected_fetcher() -> None:
    snapshot = fetch("https://example.com/data", fetcher=lambda url: "payload")
    assert snapshot.content == "payload"


def test_fetch_rejects_plain_http() -> None:
    with pytest.raises(SecurityValidationError):
        fetch("http://example.com", fetcher=lambda url: "")


def test_write_and_load_roundtrip(tmp_path: Path) -> None:
    snapshot = Snapshot.capture("https://example.com", "body", captured_at="2026-10-09T00:00:00Z")
    path = tmp_path / "snap.json"
    write(path, snapshot)
    assert load(path) == snapshot
