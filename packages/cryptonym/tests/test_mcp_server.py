"""Tests for the MCP server wiring. Skipped when the mcp SDK is absent."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("mcp")

from cryptonym import mcp_server  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DOSSIER = ROOT / "assessments" / "voltzite-vs-volt-typhoon" / "assessment.json"
ADJUDICATED = ROOT / "evaluation" / "adjudicated" / "corpus.json"


def test_assess_tool_returns_the_judgement() -> None:
    result = mcp_server.assess_dossier(str(DOSSIER))
    assert result["hypotheses_favoured"][0] == "distinct_but_overlapping"


def test_adjudicate_tool_reports_coverage_and_strict() -> None:
    result = mcp_server.adjudicate_corpus(str(ADJUDICATED), strict=True)
    assert result["coverage"]["admissible"] == 2
    assert result["strict_ok"] is True


def test_export_tool_rejects_an_unknown_format() -> None:
    assert "error" in mcp_server.export_dossier(str(DOSSIER), format="nope")


def test_reconcile_tool_exposes_the_weakest_link() -> None:
    result = mcp_server.reconcile_linkages(
        [
            {"left": "A", "right": "B", "confidence": "moderate"},
            {"left": "B", "right": "C", "confidence": "low"},
        ],
        minimum="moderate",
    )
    assert result["clusters"][0]["members"] == ["A", "B"]
    assert result["clusters"][0]["weakest_link"] == "moderate"


def test_errors_are_returned_not_raised() -> None:
    assert "error" in mcp_server.assess_dossier("/nonexistent.json")


def test_snapshot_tool_cannot_be_told_to_reach_a_private_address() -> None:
    """M6: the SSRF boundary is not an opt-out tool argument."""
    assert "error" in mcp_server.snapshot_source("http://127.0.0.1:9/source")


def test_documentation_tool_serves_the_method() -> None:
    result = mcp_server.documentation("adjudication")
    assert "external truth" in result["content"].lower()
