"""Tests for the CLI and MCP tools."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from assessment.cli import main


def test_grade_command(capsys: pytest.CaptureFixture[str]) -> None:
    pytest.importorskip("cryptonym")
    assert main(["grade", "--confidence", "high"]) == 0
    assert json.loads(capsys.readouterr().out)["confidence"] == "high"


def test_ledger_command(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["ledger", str(tmp_path / "none.jsonl")]) == 0
    assert json.loads(capsys.readouterr().out)["count"] == 0


def test_assess_command(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    pytest.importorskip("cryptonym")
    document = {
        "question": "?",
        "hypotheses": ["a", "b"],
        "evidence": [
            {"id": "E1", "statement": "x", "source": "s", "type": "tactics", "consistency": {"a": "C", "b": "I"}}
        ],
        "judgement": {"confidence": "moderate"},
    }
    path = tmp_path / "claim.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    assert main(["assess", str(path)]) == 0
    assert json.loads(capsys.readouterr().out)["ranking"] == ["a", "b"]


def test_mcp_tools() -> None:
    pytest.importorskip("cryptonym")
    from assessment import mcp_server

    assert mcp_server.grade_claim("high")["confidence"] == "high"
    assert "ranking" in mcp_server.weigh_evidence(
        [{"id": "E1", "statement": "x", "source": "s", "type": "tactics", "consistency": {"a": "C"}}], ["a"]
    )
