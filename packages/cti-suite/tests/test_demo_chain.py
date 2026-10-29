"""The demo is a test: the chain is in the data, not in the prose."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "demo" / "out"


@pytest.fixture(scope="module")
def demo_run() -> dict:
    result = subprocess.run(["/bin/sh", "demo/run.sh"], cwd=ROOT, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    return {
        "stdout": result.stdout,
        "bundle": json.loads((OUT / "bundle.json").read_text(encoding="utf-8")),
        "hunt": json.loads((OUT / "hunt.json").read_text(encoding="utf-8")),
        "verdict": json.loads((OUT / "verdict.json").read_text(encoding="utf-8")),
        "report": (OUT / "product.md").read_text(encoding="utf-8"),
        "gate": json.loads((OUT / "gate.json").read_text(encoding="utf-8")),
    }


def test_the_bundle_carries_the_trace_of_the_steps_before_it(demo_run: dict) -> None:
    from cti_method.trace import content_hash

    report = next(obj for obj in demo_run["bundle"]["objects"] if obj["type"] == "report")
    references = {item["source_name"]: item["external_id"] for item in report["external_references"]}
    ids = {kind: value.split("@")[0] for kind, value in references.items()}
    assert ids == {
        "cti-suite:pir": "PIR-001",
        "cti-suite:assessment": "nightjar-vs-saltwind",
        "cti-suite:hunt": "HUNT-001",
    }
    # The hash pins the exact content of the judgement, not just its id.
    assert references["cti-suite:assessment"].split("@")[1] == content_hash(demo_run["verdict"])


def test_the_hunt_plan_cites_the_assessment_and_uses_attack_v18_plus(demo_run: dict) -> None:
    assert demo_run["hunt"]["id"] == "HUNT-001"
    assert demo_run["hunt"]["assessment_id"] == "nightjar-vs-saltwind"
    assert demo_run["hunt"]["attack"]["attack_version"] >= "18"
    for technique in demo_run["hunt"]["techniques"]:
        assert technique["detection_strategies"], technique["technique_id"]


def test_the_second_run_reproduces_the_first_judgement(demo_run: dict) -> None:
    assert demo_run["verdict"]["reproduced"] is True
    assert demo_run["verdict"]["grade"]["confidence"] == "low"
    assert demo_run["verdict"]["ceiling"] == "moderate"


def test_the_gate_passes_the_product_it_built(demo_run: dict) -> None:
    assert demo_run["gate"]["shareable"] is True
    assert demo_run["gate"]["effective_tlp"] == "TLP:AMBER"


def test_the_report_reads_as_one_product(demo_run: dict) -> None:
    report = demo_run["report"]
    assert "# NIGHTJAR" in report
    assert "> TLP:AMBER" in report
    assert "PIR-001" in report
    assert "the evidence supports at most **moderate**" in report
    assert "detection strategies" in report
    assert "cti-suite:assessment=nightjar-vs-saltwind@" in report
    assert "does not contain" not in report
