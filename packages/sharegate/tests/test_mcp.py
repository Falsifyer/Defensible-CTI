"""Tests for the ShareGate MCP tools. Skipped when the mcp SDK is absent."""

from __future__ import annotations

import pytest

pytest.importorskip("mcp")

from cti_method.stix import TLP  # noqa: E402

from sharegate import mcp_server  # noqa: E402


def _bundle() -> dict:
    marking = {
        "type": "marking-definition",
        "spec_version": "2.1",
        "id": TLP["CLEAR"]["id"],
        "created": "2022-10-01T00:00:00.000Z",
        "name": "TLP:CLEAR",
        "extensions": {
            "extension-definition--60a3c5c5-0d10-413e-aab3-9e08dde9e88d": {
                "extension_type": "property-extension",
                "tlp_2_0": "clear",
            }
        },
    }
    return {
        "type": "bundle",
        "id": "bundle--11111111-1111-4111-8111-111111111111",
        "objects": [
            marking,
            {
                "type": "indicator",
                "spec_version": "2.1",
                "id": "indicator--22222222-2222-4222-8222-222222222222",
                "created": "2026-10-09T00:00:00Z",
                "modified": "2026-10-09T00:00:00Z",
                "pattern": "[ipv4-addr:value = '192.0.2.1']",
                "pattern_type": "stix",
                "valid_from": "2026-10-09T00:00:00Z",
                "object_marking_refs": [marking["id"]],
            },
        ],
    }


def test_tlp_policy_table_tool() -> None:
    assert mcp_server.tlp_policy_table()


def test_check_tlp_marking_tool() -> None:
    assert mcp_server.check_tlp_marking("TLP:AMBER")["effective"] == "TLP:AMBER"


def test_check_stix_bundle_tool() -> None:
    result = mcp_server.check_stix_bundle(_bundle())
    assert result["valid"] is True


def test_check_stix_bundle_tool_reports_breakage() -> None:
    result = mcp_server.check_stix_bundle({"type": "bundle", "id": "bundle--x", "objects": []})
    assert result["valid"] is False


def test_pre_share_check_refuses_a_conflict() -> None:
    result = mcp_server.pre_share_check("TLP:CLEAR and TLP:RED")
    assert result["shareable"] is False


def test_pre_share_check_flags_a_sensitive_permissive_product() -> None:
    result = mcp_server.pre_share_check("TLP:CLEAR\nvictim@example.com 10.0.0.1")
    assert "tlp-sensitive-permissive" in {item["code"] for item in result["findings"]}
