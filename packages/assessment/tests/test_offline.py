"""Offline tests: these run even without the shared core installed."""

from __future__ import annotations

from pathlib import Path

from assessment.core import append_claim, method_documentation, read_ledger


def test_reading_a_missing_ledger_is_empty(tmp_path: Path) -> None:
    result = read_ledger(str(tmp_path / "none.jsonl"))
    assert result["count"] == 0
    assert result["claims"] == []


def test_append_then_read_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "ledger" / "claims.jsonl"
    append_claim(str(path), {"id": "c1", "confidence": "moderate"})
    append_claim(str(path), {"id": "c2", "confidence": "high"})
    result = read_ledger(str(path))
    assert result["count"] == 2
    assert result["claims"][1]["id"] == "c2"


def test_method_documentation_is_available_from_the_repository() -> None:
    result = method_documentation("method")
    assert "cryptonym.method" in result["content"] or "shared core" in result["content"]
