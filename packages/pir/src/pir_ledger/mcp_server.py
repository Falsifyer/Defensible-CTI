"""pir-ledger as an MCP server: the first step of the cycle, reachable by an agent."""

from __future__ import annotations

from typing import Any

from cti_method.contract import read_json
from mcp.server.mcpserver import MCPServer

from pir_ledger import __version__
from pir_ledger.validate import validate

server = MCPServer(
    name="pir",
    title="PIR Ledger",
    version=__version__,
    instructions=(
        "A PIR is a question tied to a decision. This server validates a register of "
        "PIR -> EEI -> indicator and returns the requirement identifiers the rest of the "
        "cycle cites."
    ),
)


@server.tool()
def validate_register(path: str) -> dict[str, Any]:
    """Validate a register file; a requirement with no decision is a high finding."""
    document = read_json(path)
    if not isinstance(document, dict):
        return {"valid": False, "findings": [{"code": "not-an-object", "severity": "high",
                                              "message": "the register is not a JSON object"}]}
    return validate(document)


@server.tool()
def list_requirements(path: str, today: str | None = None) -> list[dict[str, Any]]:
    """List the requirements with their decision, consumer and deadline."""
    import datetime as dt

    document = read_json(path)
    reference = dt.date.fromisoformat(today) if today else dt.date.today()
    items = []
    for pir in document.get("requirements", []) if isinstance(document, dict) else []:
        if not isinstance(pir, dict):
            continue
        days_left = None
        try:
            days_left = (dt.date.fromisoformat(str(pir.get("deadline"))) - reference).days
        except (TypeError, ValueError):
            pass
        items.append(
            {
                "id": pir.get("id"),
                "question": pir.get("question"),
                "decision": pir.get("decision"),
                "consumer": pir.get("consumer"),
                "priority": pir.get("priority"),
                "deadline": pir.get("deadline"),
                "days_left": days_left,
                "status": pir.get("status", "open"),
            }
        )
    return items


@server.tool()
def requirement_ids(path: str) -> list[str]:
    """The requirement identifiers a dossier cites as requirement_id."""
    document = read_json(path)
    if not isinstance(document, dict):
        return []
    return [str(item["id"]) for item in document.get("requirements", []) if isinstance(item, dict) and item.get("id")]


@server.tool()
def register_contract() -> dict[str, Any]:
    """The rules this register enforces."""
    return {
        "rules": [
            {"code": "no-decision", "severity": "high", "rule": "a requirement must name the decision it informs"},
            {"code": "no-consumer", "severity": "high", "rule": "a requirement must name who takes that decision"},
            {"code": "indicator-ungraded", "severity": "high", "rule": "every indicator carries an Admiralty grade (A-F + 1-6)"},
            {"code": "bad-admiralty", "severity": "medium", "rule": "the grade must be A-F followed by 1-6"},
        ],
        "exit_codes": {"0": "valid", "1": "high finding", "2": "could not check"},
    }


def main() -> None:
    """Entry point: run the MCP server over standard input/output."""
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
