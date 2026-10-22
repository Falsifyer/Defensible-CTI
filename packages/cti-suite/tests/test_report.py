"""The report's BLUF and its completeness rule."""

from __future__ import annotations

import json
from pathlib import Path

from cti_suite.cli import main
from cti_suite.report import missing_artifacts, render_report

ROOT = Path(__file__).resolve().parents[3]


def _load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _verdict() -> dict:
    return {
        "id": "nightjar-vs-saltwind",
        "requirement_id": "PIR-001",
        "question": "Are NIGHTJAR and SALTWIND the same actor?",
        "ranking": ["distinct_but_overlapping", "brokered_shared_access", "same_actor"],
        "inconsistencies": {"same_actor": 2, "distinct_but_overlapping": 0, "brokered_shared_access": 0},
        "discriminating": ["E1", "E3", "E6"],
        "consistent_with_everything": ["E2", "E4", "E5"],
        "grade": {"confidence": "low"},
        "ceiling": "moderate",
        "grade_reasons": [
            "3 diagnostic item(s) discriminate (E1, E3, E6)",
            "diagnostic evidence comes from a single source: moderate is the ceiling",
        ],
        "review_trigger": "A vendor split, or infrastructure that links both sets at once",
        "review_by": "2027-04-30",
        "findings": [],
    }


def test_the_report_opens_with_a_bottom_line_built_from_the_judgement() -> None:
    text = render_report(
        pir=_load("demo/pir.json"),
        assessment={**_load("demo/assessment.json"), **_verdict()},
        marking="TLP:CLEAR",
    )
    head = text[: text.index("## Requirement")]
    assert "## Bottom line" in head
    assert "favours **distinct_but_overlapping**" in head
    assert "declares **low** confidence" in head
    assert "supports at most **moderate**" in head
    assert "diagnostic evidence comes from a single source" in head
    assert "What would change it: A vendor split" in head
    assert "Review by: 2027-04-30" in head


def test_a_refused_grade_says_so_in_the_bottom_line() -> None:
    verdict = _verdict()
    verdict["findings"] = [{"code": "grade-exceeds-evidence", "severity": "high", "message": "x"}]
    verdict["grade"] = {"confidence": "high"}
    text = render_report(assessment={**_load("demo/assessment.json"), **verdict})
    assert "The declaration exceeds the evidence and the tool refuses it." in text


def test_missing_artifacts_are_named() -> None:
    missing = missing_artifacts(pir=_load("demo/pir.json"))
    assert missing == ["assessment", "hunt plan", "product"]
    assert "No hunt plan was supplied" in render_report(pir=_load("demo/pir.json"))


def test_require_complete_refuses_an_incomplete_report(tmp_path: Path, capsys) -> None:
    output = tmp_path / "product.md"
    assert main(["report", "--pir", str(ROOT / "demo/pir.json"), "-o", str(output)]) == 0
    capsys.readouterr()
    assert main(["report", "--pir", str(ROOT / "demo/pir.json"), "--require-complete", "-o", str(output)]) == 1
    assert "incomplete" in capsys.readouterr().err
