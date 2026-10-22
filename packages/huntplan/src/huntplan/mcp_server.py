"""HuntPlan as an MCP server."""

from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer

from huntplan import __version__
from huntplan.core import assess_hunt_maturity, build_hunt_plan, data_sources_for, hmm_levels, validate_hypothesis

server = MCPServer(
    name="huntplan",
    title="HuntPlan",
    version=__version__,
    instructions=(
        "Threat-hunting method: a falsifiable If/then hypothesis, the ATT&CK data sources "
        "that would satisfy it, a closure criterion, and a maturity assessment."
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
def data_sources_for_technique(technique_id: str) -> dict[str, Any]:
    """Return the required data sources for an ATT&CK technique (curated subset)."""
    return data_sources_for(technique_id)


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


def main() -> None:
    """Entry point: run the MCP server over standard input/output."""
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
