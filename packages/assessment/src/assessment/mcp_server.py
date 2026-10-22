"""assessment-mcp as an MCP server: a ledger of graded judgements."""

from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer

from assessment import __version__
from assessment.core import (
    append_claim,
    assess,
    calibrate,
    filter_truth,
    grade,
    method_documentation,
    read_ledger,
    weigh,
)

server = MCPServer(
    name="assessment",
    title="Assessment Ledger",
    version=__version__,
    instructions=(
        "Grade any claim: two-axis confidence, ACH over arbitrary hypotheses, and an "
        "external truth that must be earned from independent sources. Built on cryptonym.method."
    ),
)


@server.tool()
def grade_claim(confidence: str, probability: str | None = None) -> dict[str, Any]:
    """Grade a claim on two independent axes: confidence, and probability where estimative."""
    return grade(confidence, probability)


@server.tool()
def weigh_evidence(evidence: list[dict[str, Any]], hypotheses: list[str] | None = None) -> dict[str, Any]:
    """Compare competing hypotheses against evidence (ACH); hypotheses may be any labels."""
    return weigh(evidence, hypotheses)


@server.tool()
def filter_external_truth(adjudication: dict[str, Any]) -> dict[str, Any]:
    """Apply the external-truth filter: is a declared truth earned from independent sources?"""
    return filter_truth(adjudication)


@server.tool()
def assess_document(document: dict[str, Any]) -> dict[str, Any]:
    """Grade a full claim (evidence + hypotheses + grade, optional adjudication)."""
    return assess(document)


@server.tool()
def append_claim_to_ledger(path: str, claim: dict[str, Any]) -> dict[str, Any]:
    """Append a graded claim to a ledger (JSON Lines file)."""
    return append_claim(path, claim)


@server.tool()
def read_ledger_file(path: str) -> dict[str, Any]:
    """Read a ledger (JSON Lines) of graded claims."""
    return read_ledger(path)


@server.tool()
def calibrate_cases(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Score labelled claims: false-merge rate, false-split rate and calibration."""
    return calibrate(cases)


@server.tool()
def method_docs(section: str = "method") -> dict[str, Any]:
    """Return one of this tool's method documents."""
    return method_documentation(section)


def main() -> None:
    """Entry point: run the MCP server over standard input/output."""
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
