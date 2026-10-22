"""ShareGate as an MCP server: a pre-share compliance gate an agent can call."""

from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer

from sharegate import __version__
from sharegate.core import check_stix, check_tlp, pre_share, tlp_policy

server = MCPServer(
    name="sharegate",
    title="ShareGate",
    version=__version__,
    instructions=(
        "Pre-share compliance gate for CTI: TLP 2.0 correctness and STIX 2.1 conformance, "
        "judged against external schemas. shareable is false only on a high-severity finding."
    ),
)


@server.tool()
def tlp_policy_table() -> list[dict[str, Any]]:
    """Return the FIRST TLP 2.0 policy table (the ground truth this gate applies)."""
    return tlp_policy()


@server.tool()
def check_tlp_marking(text: str) -> dict[str, Any]:
    """Check a product's TLP marking.

    Flags a missing marking, conflicting markings, the deprecated TLP:WHITE, and a
    permissive marking (CLEAR/GREEN) on content that looks sensitive.
    """
    return check_tlp(text)


@server.tool()
def check_stix_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    """Check a STIX 2.1 bundle for structural conformance.

    Flags a non-bundle top level, a missing objects array, objects without type or id, an
    id whose prefix does not match its type, duplicate ids, and a wrong or missing
    spec_version.
    """
    return check_stix(bundle)


@server.tool()
def pre_share_check(document: str) -> dict[str, Any]:
    """Run the full gate on a product (a STIX bundle as JSON, or any text).

    ``shareable`` is False only when a high-severity finding is present.
    """
    return pre_share(document)


def main() -> None:
    """Entry point: run the MCP server over standard input/output."""
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
