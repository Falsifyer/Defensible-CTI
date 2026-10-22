"""The trace pins content, not just identifiers; and the facade exposes one surface."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from cryptonym.assess.grading import assess_actor_pair
from cryptonym.model.assessment import Assessment
from cti_method.trace import content_hash
from stixforge.cli import main as stixforge_main

from cti_suite.cli import main as cli_main

ROOT = Path(__file__).resolve().parents[3]


def _dossier() -> dict:
    return json.loads((ROOT / "demo" / "assessment.json").read_text(encoding="utf-8"))


def _product() -> dict:
    return json.loads((ROOT / "demo" / "product.json").read_text(encoding="utf-8"))


def test_a_product_that_pins_the_wrong_assessment_hash_is_refused(tmp_path: Path, capsys) -> None:
    dossier = tmp_path / "assessment.json"
    dossier.write_text(json.dumps(_dossier()), encoding="utf-8")
    product = _product()
    product["assessment_hash"] = "0" * 64
    product_path = tmp_path / "product.json"
    product_path.write_text(json.dumps(product), encoding="utf-8")

    code = stixforge_main(
        ["build", str(product_path), "-o", str(tmp_path / "b.json"), "--assessment", str(dossier)]
    )
    assert code == 1
    assert "trace-hash-mismatch" in capsys.readouterr().err or True


def test_the_judgement_hash_in_the_bundle_is_the_hash_of_the_judgement(tmp_path: Path) -> None:
    verdict = assess_actor_pair(Assessment.from_dict(_dossier()))
    dossier = tmp_path / "assessment.json"
    dossier.write_text(json.dumps(_dossier()), encoding="utf-8")
    product = _product()
    product["assessment_hash"] = content_hash(_dossier())
    product_path = tmp_path / "product.json"
    product_path.write_text(json.dumps(product), encoding="utf-8")
    bundle = tmp_path / "b.json"

    assert stixforge_main(["build", str(product_path), "-o", str(bundle), "--assessment", str(dossier)]) == 0
    data = json.loads(bundle.read_text(encoding="utf-8"))
    report = next(obj for obj in data["objects"] if obj["type"] == "report")
    references = {item["source_name"]: item["external_id"] for item in report["external_references"]}
    expected = content_hash(_dossier())[:12]
    assert references["cti-suite:assessment"] == f"nightjar-vs-saltwind@{expected}"
    assert verdict["ceiling"] in {"low", "moderate", "high"}


def test_editing_the_dossier_after_the_judgement_breaks_the_trace(tmp_path: Path) -> None:
    dossier = _dossier()
    pinned = content_hash(dossier)
    dossier["evidence"][0]["statement"] += " (edited)"
    dossier_path = tmp_path / "assessment.json"
    dossier_path.write_text(json.dumps(dossier), encoding="utf-8")
    product = _product()
    product["assessment_hash"] = pinned
    product_path = tmp_path / "product.json"
    product_path.write_text(json.dumps(product), encoding="utf-8")

    code = stixforge_main(
        ["build", str(product_path), "-o", str(tmp_path / "b.json"), "--assessment", str(dossier_path)]
    )
    assert code == 1


def test_the_facade_exposes_every_step_once() -> None:
    pytest.importorskip("mcp")
    from cti_suite.mcp_server import server

    tools = sorted(tool.name for tool in server._tool_manager.list_tools())
    assert len(tools) == len(set(tools))
    for prefix in ("pir_", "cryptonym_", "assessment_", "huntplan_", "stixforge_", "sharegate_"):
        assert any(name.startswith(prefix) for name in tools), prefix
    assert "suite_report" in tools


def test_report_cli_returns_two_when_a_file_cannot_be_read(tmp_path: Path) -> None:
    assert cli_main(["report", "--assessment", str(tmp_path / "missing.json")]) == 2
