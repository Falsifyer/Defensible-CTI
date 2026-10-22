"""HuntPlan as an MCP server."""

from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer

from huntplan import __version__
from huntplan.core import (
    assess_hunt_maturity,
    attack_provenance,
    build_hunt_plan,
    detections_for,
    hmm_levels,
    validate_hypothesis,
    validate_plan,
)

server = MCPServer(
    name="huntplan",
    title="HuntPlan",
    version=__version__,
    instructions=(
        "Threat-hunting method: a falsifiable If/then hypothesis, the ATT&CK v18+ detection "
        "strategies that would satisfy it (data sources were deprecated), a closure "
        "criterion, and a maturity assessment."
    ),
)


@server.tool()
def hmm_levels_table() -> list[dict[str, Any]]:
    """Return the Hunting Maturity Model levels (0 Initial … 4 Leading)."""
    return hmm_levels()


@server.tool()
def validate_hypothesis_text(text: str) -> dict[str, Any]:
    """Check a hypothesis is falsifiable (If … then …), names telemetry, and is not hedged."""
    return validate_hypothesis(text)


@server.tool()
def detection_strategies_for_technique(technique_id: str) -> dict[str, Any]:
    """Return the ATT&CK detection strategies, analytics and data components for a technique."""
    return detections_for(technique_id)


@server.tool()
def data_sources_for_technique(technique_id: str) -> dict[str, Any]:
    """Deprecated name: ATT&CK v18 deprecated data sources. Returns detection strategies."""
    return detections_for(technique_id) | {
        "deprecated": "ATT&CK v18 deprecated Data Sources; this returns detection strategies"
    }


@server.tool()
def attack_map_provenance() -> dict[str, Any]:
    """The ATT&CK collection version the shipped map was generated from."""
    return attack_provenance()


@server.tool()
def assess_maturity(factors: dict[str, bool]) -> dict[str, Any]:
    """Return the HMM level earned by programme factors.

    Factors: structured_data, documented_procedures, analyst_hypotheses,
    automated_detection. Each level requires the one below it.
    """
    return assess_hunt_maturity(factors)


@server.tool()
def build_plan(
    question: str,
    hypothesis: str,
    techniques: list[str] | None = None,
    closure: str = "",
    actor: str = "",
) -> dict[str, Any]:
    """Assemble a hunt plan and state whether it is ready to run."""
    return build_hunt_plan(question, hypothesis, techniques, closure, actor)


@server.tool()
def validate_plan_document(plan: dict[str, Any]) -> dict[str, Any]:
    """Validate a hunt plan document: falsifiable hypothesis, closure criterion, technique."""
    return validate_plan(plan)


def main() -> None:
    """Entry point: run the MCP server over standard input/output."""
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
