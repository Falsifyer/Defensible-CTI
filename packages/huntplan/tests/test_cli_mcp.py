"""Tests for the HuntPlan CLI and MCP tools."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from huntplan.cli import main


def test_hmm_command(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["hmm"]) == 0
    assert len(json.loads(capsys.readouterr().out)) == 5


def test_validate_command(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    good = tmp_path / "h.txt"
    good.write_text(
        "If scheduled tasks are created, then process creation logs will show schtasks.exe",
        encoding="utf-8",
    )
    assert main(["validate", str(good)]) == 0

    bad = tmp_path / "b.txt"
    bad.write_text("look around", encoding="utf-8")
    assert main(["validate", str(bad)]) == 1


def test_sources_command_known_and_unknown(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["sources", "T1059"]) == 0
    assert main(["sources", "T9999"]) == 1


def test_mcp_tools() -> None:
    pytest.importorskip("mcp")
    from huntplan import mcp_server

    assert len(mcp_server.hmm_levels_table()) == 5
    assert mcp_server.validate_hypothesis_text("If x then y in process logs")["falsifiable"] is True
    assert mcp_server.data_sources_for_technique("T1059")["known"] is True
    assert mcp_server.assess_maturity({"structured_data": True})["level"] == 1
    plan = mcp_server.build_plan("q", "If x then y in dns logs", ["T1071"], "confirmed or refuted")
    assert plan["ready"] is True
