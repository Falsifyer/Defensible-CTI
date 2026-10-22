"""Tests for the ShareGate MCP tools. Skipped when the mcp SDK is absent."""

from __future__ import annotations

import pytest

pytest.importorskip("mcp")

from sharegate import mcp_server  # noqa: E402


def test_tlp_policy_table_tool() -> None:
    assert mcp_server.tlp_policy_table()


def test_check_tlp_marking_tool() -> None:
    assert mcp_server.check_tlp_marking("TLP:AMBER")["effective"] == "TLP:AMBER"


def test_check_stix_bundle_tool() -> None:
    result = mcp_server.check_stix_bundle({"type": "bundle", "id": "bundle--x", "objects": []})
    assert result["valid"] is True


def test_pre_share_check_blocks_a_leak() -> None:
    result = mcp_server.pre_share_check("TLP:CLEAR\nvictim@example.com 10.0.0.1")
    assert result["shareable"] is False
