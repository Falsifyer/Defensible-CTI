"""ctisuite-mcp — one MCP server for the whole cycle.

Six servers with overlapping tool names (`validate` three times, `assess` twice) is not a
product: the client has to know which one to call. This facade exposes the six under
prefixed names and adds the two cross-cutting tools, ``suite_report`` and
``suite_trace``. It is a thin layer: every tool calls the same function the CLI calls.
"""

from __future__ import annotations

from typing import Any

from assessment import core as assessment_core
from cryptonym.assess.grading import assess_actor_pair
from cryptonym.model.assessment import load_assessment
from cti_method.contract import read_json
from cti_method.stix import effective_marking
from huntplan.core import detections_for, validate_plan
from mcp.server.mcpserver import MCPServer
from pir_ledger.validate import validate as pir_validate
from sharegate.core import pre_share
from stixforge.build import build
from stixforge.validate import validate as stix_validate

from cti_suite import __version__
from cti_suite.report import render_report

server = MCPServer(
    name="ctisuite",
    title="cti-suite",
    version=__version__,
    instructions=(
        "One intelligence cycle: requirements (pir), alias judgement (cryptonym), graded "
        "ledger (assessment), hunt plan (huntplan), STIX product (stixforge) and pre-share "
        "gate (sharegate). Every tool returns findings and obeys 0/1/2 at the CLI."
    ),
)


@server.tool()
def pir_validate_register(path: str) -> dict[str, Any]:
    """Validate a PIR register: no decision, no PIR."""
    document = read_json(path)
    return pir_validate(document) if isinstance(document, dict) else {"valid": False}


@server.tool()
def cryptonym_assess(path: str) -> dict[str, Any]:
    """Re-derive the graded alias judgement, including the evidence-derived ceiling."""
    return assess_actor_pair(load_assessment(path))


@server.tool()
def assessment_assess(path: str) -> dict[str, Any]:
    """Grade any claim: ranking, ceiling, declared grade and findings."""
    document = read_json(path)
    return assessment_core.assess(document) if isinstance(document, dict) else {"findings": []}


@server.tool()
def huntplan_validate(path: str) -> dict[str, Any]:
    """Validate a hunt plan (falsifiable hypothesis, closure criterion, technique)."""
    document = read_json(path)
    return validate_plan(document) if isinstance(document, dict) else {"ready": False}


@server.tool()
def huntplan_detections(technique_id: str) -> dict[str, Any]:
    """ATT&CK detection strategies and data components for a technique (curated subset)."""
    return detections_for(technique_id)


@server.tool()
def stixforge_build(product_path: str, trace: dict[str, str | None] | None = None) -> dict[str, Any]:
    """Build a STIX 2.1 bundle from a product JSON file."""
    document = read_json(product_path)
    return build(document, trace=trace) if isinstance(document, dict) else {"objects": []}


@server.tool()
def stixforge_validate(bundle_path: str, today: str | None = None) -> dict[str, Any]:
    """Validate a STIX 2.1 bundle with the suite's single validator."""
    return stix_validate(read_json(bundle_path), today=today)


@server.tool()
def sharegate_check(path: str) -> dict[str, Any]:
    """The pre-share gate: TLP 2.0 and STIX 2.1."""
    return pre_share(read_json(path))


@server.tool()
def suite_report(
    pir_path: str | None = None,
    assessment_path: str | None = None,
    verdict_path: str | None = None,
    hunt_path: str | None = None,
    product_path: str | None = None,
    bundle_path: str | None = None,
) -> str:
    """Render the cycle as one markdown product from the artifacts that exist."""
    pir = read_json(pir_path) if pir_path else None
    dossier = read_json(assessment_path) if assessment_path else None
    verdict = read_json(verdict_path) if verdict_path else None
    hunt = read_json(hunt_path) if hunt_path else None
    product = read_json(product_path) if product_path else None
    bundle = read_json(bundle_path) if bundle_path else None
    combined = dict(dossier or {})
    combined.update(verdict or {})
    label = effective_marking(bundle) if bundle else None
    return render_report(
        pir=pir,
        assessment=combined or None,
        hunt=hunt,
        product=product,
        bundle=bundle,
        marking=f"TLP:{label}" if label else None,
    )


def main() -> None:
    """Entry point: run the MCP server over standard input/output."""
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
