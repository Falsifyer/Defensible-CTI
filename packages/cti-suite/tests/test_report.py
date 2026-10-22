"""The report is a rendering, not a second opinion: it may not invent a number."""

from __future__ import annotations

import json
from pathlib import Path

from cti_suite.report import render_report

ROOT = Path(__file__).resolve().parents[3]


def _load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_the_report_repeats_the_ceiling_and_never_upgrades_the_grade() -> None:
    assessment = _load("demo/assessment.json")
    verdict = {
        "id": "nightjar-vs-saltwind",
        "requirement_id": "PIR-001",
        "hypotheses_favoured": ["distinct_but_overlapping", "brokered_shared_access", "same_actor"],
        "inconsistencies": {"same_actor": 2, "distinct_but_overlapping": 0, "brokered_shared_access": 0},
        "discriminating_evidence": ["E1", "E3", "E6"],
        "consistent_with_everything": ["E2", "E4", "E5"],
        "grade": {"confidence": "low"},
        "ceiling": "moderate",
    }
    text = render_report(pir=_load("demo/pir.json"), assessment={**assessment, **verdict}, marking="TLP:CLEAR")
    assert "declared confidence: low" in text
    assert "supports at most **moderate**" in text
    assert "E2, E4, E5" in text
    assert "PIR-001" in text


def test_missing_artifacts_are_named_as_gaps() -> None:
    text = render_report(assessment={"question": "q", "hypotheses_favoured": ["a"], "grade": {"confidence": "low"}})
    assert "does not contain" in text
    assert "No requirement register was supplied" in text
    assert "No hunt plan was supplied" in text


def test_the_report_has_no_numbers_of_its_own() -> None:
    """Without an assessment there is no ceiling to print."""
    text = render_report(pir=_load("demo/pir.json"))
    assert "supports at most" not in text
    assert "## Judgement" not in text
