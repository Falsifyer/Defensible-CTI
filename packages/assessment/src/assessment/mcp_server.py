"""assessment-mcp as an MCP server: a ledger of graded judgements."""

from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer

from assessment import __version__
from assessment.core import (
    append_claim,
    assess,
    calibrate,
    ceiling_for,
    filter_truth,
    grade,
    method_documentation,
    read_ledger,
    verify_ledger,
    weigh,
)

server = MCPServer(
    name="assessment",
    title="Assessment Ledger",
    version=__version__,
    instructions=(
        "Grade any claim: two-axis confidence, ACH over arbitrary hypotheses, a ceiling "
        "derived from the evidence, and an external truth that must be earned from "
        "independent sources. Built on cti-method."
    ),
)


@server.tool()
def grade_claim(confidence: str, probability: str | None = None) -> dict[str, Any]:
    """Grade a claim on two independent axes: confidence, and probability where estimative."""
    return grade(confidence, probability)


@server.tool()
def weigh_evidence(evidence: list[dict[str, Any]], hypotheses: list[str]) -> dict[str, Any]:
    """Compare competing hypotheses against evidence (ACH); hypotheses may be any labels.

    At least two hypotheses are required: one option is not analysis.
    """
    return weigh(evidence, hypotheses)


@server.tool()
def filter_external_truth(adjudication: dict[str, Any]) -> dict[str, Any]:
    """Apply the external-truth filter: independence, standard, contested."""
    return filter_truth(adjudication)


@server.tool()
def assess_document(document: dict[str, Any]) -> dict[str, Any]:
    """Grade a whole claim: ranking, ceiling, declared grade and findings."""
    return assess(document)


@server.tool()
def grade_ceiling(evidence: list[dict[str, Any]]) -> dict[str, Any]:
    """The strongest confidence this evidence can support, and why."""
    return ceiling_for(evidence)


@server.tool()
def append_claim_to_ledger(
    path: str,
    claim: dict[str, Any],
    tool: str = "assessment",
    now: str | None = None,
    head_out: str | None = None,
) -> dict[str, Any]:
    """Append a graded claim to a hash-chained ledger, creating it if needed."""
    return append_claim(path, claim, tool=tool, now=now, head_out=head_out)


@server.tool()
def read_ledger_file(path: str) -> dict[str, Any]:
    """Read a ledger (JSON Lines) of graded claims."""
    return read_ledger(path)


@server.tool()
def verify_ledger_file(
    path: str,
    expected_head: str | None = None,
    expected_count: int | None = None,
    head_file: str | None = None,
) -> dict[str, Any]:
    """Verify the chain, and its head/length when an anchor is supplied."""
    return verify_ledger(
        path,
        expected_head=expected_head,
        expected_count=expected_count,
        head_file=head_file,
    )


@server.tool()
def calibrate_cases(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Score labelled calls: confusion, false-merge rate and calibration by confidence."""
    return calibrate(cases)


@server.tool()
def method_docs(section: str = "method") -> dict[str, Any]:
    """Return one of this tool's method documents, from the installed package."""
    return method_documentation(section)


def main() -> None:
    """Entry point: run the MCP server over standard input/output."""
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
