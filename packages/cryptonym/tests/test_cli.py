"""Tests for the command-line interface."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cryptonym.cli import main

DOSSIER = Path(__file__).resolve().parents[1] / "assessments" / "voltzite-vs-volt-typhoon" / "assessment.json"


def test_assess_prints_judgement(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["assess", str(DOSSIER)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["hypotheses_favoured"][0] == "distinct_but_overlapping"
    assert payload["inconsistencies"]["same_actor"] == 4


def test_render_writes_markdown(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["render", str(DOSSIER)]) == 0
    assert "## Consistency matrix" in capsys.readouterr().out


def test_export_stix(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["export", str(DOSSIER), "--format", "stix"]) == 0
    assert json.loads(capsys.readouterr().out)["type"] == "bundle"


def test_export_taxii(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["export", str(DOSSIER), "--format", "taxii"]) == 0
    assert json.loads(capsys.readouterr().out)["more"] is False


def test_export_misp(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["export", str(DOSSIER), "--format", "misp"]) == 0
    assert json.loads(capsys.readouterr().out)["aliases_assessed_not_asserted"] is True


def test_ingest_misp_galaxy(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    source = tmp_path / "galaxy.json"
    source.write_text(json.dumps({"values": [{"value": "APT28", "meta": {"synonyms": ["Sofacy"]}}]}), encoding="utf-8")
    assert main(["ingest", "--source", "misp-galaxy", "--input", str(source)]) == 0
    names = [item["name"] for item in json.loads(capsys.readouterr().out)]
    assert names == ["APT28", "Sofacy"]


def test_missing_dossier_returns_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["assess", str(tmp_path / "nope.json")]) == 2
    assert "error:" in capsys.readouterr().err
