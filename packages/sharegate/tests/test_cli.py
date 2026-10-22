"""Tests for the ShareGate command-line interface."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sharegate.cli import main


def test_policy_command(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["policy"]) == 0
    table = json.loads(capsys.readouterr().out)
    assert any(row["marking"] == "TLP:RED" for row in table)


def test_tlp_command_passes_a_clean_product(tmp_path: Path) -> None:
    path = tmp_path / "product.md"
    path.write_text("TLP:AMBER\nvictim infrastructure", encoding="utf-8")
    assert main(["tlp", str(path)]) == 0


def test_tlp_command_flags_a_missing_marking(tmp_path: Path) -> None:
    path = tmp_path / "product.md"
    path.write_text("no handling caveat", encoding="utf-8")
    assert main(["tlp", str(path)]) == 1


def test_check_command_blocks_an_unshareable_bundle(tmp_path: Path) -> None:
    path = tmp_path / "bundle.json"
    path.write_text(
        json.dumps({"type": "bundle", "id": "bundle--x", "objects": [{"type": "indicator", "id": "wrong--a"}]}),
        encoding="utf-8",
    )
    assert main(["check", str(path)]) == 1


def test_check_command_passes_a_clean_product(tmp_path: Path) -> None:
    path = tmp_path / "product.md"
    path.write_text("TLP:RED\nfor your eyes only", encoding="utf-8")
    assert main(["check", str(path)]) == 0
