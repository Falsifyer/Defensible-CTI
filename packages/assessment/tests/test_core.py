"""Tests that consume the shared core. Skipped when cryptonym is not installed."""

from __future__ import annotations

import pytest

pytest.importorskip("cryptonym")

from assessment.core import assess, calibrate, filter_truth, grade, weigh  # noqa: E402


def test_grade_carries_two_independent_axes() -> None:
    result = grade("low", "very_likely")
    assert result["two_axis"] is True
    assert result["confidence"] == "low"
    assert result["probability"] == "very_likely"


def test_weigh_accepts_arbitrary_hypothesis_labels() -> None:
    evidence = [
        {
            "id": "E1",
            "statement": "the actor used a unique implant",
            "source": "reporting",
            "type": "code",
            "consistency": {"compromise": "C", "false-alarm": "I"},
        }
    ]
    result = weigh(evidence, ["false-alarm", "compromise"])
    assert result["ranking"] == ["compromise", "false-alarm"]
    assert result["inconsistencies"] == {"false-alarm": 1, "compromise": 0}
    assert result["matrix"]["E1"]["compromise"] == "C"


def test_filter_truth_requires_independent_sources() -> None:
    adjudication = {
        "truth": "same_actor",
        "standard": "vendor-consensus",
        "sources": [
            {"publisher": "A", "url": "https://a", "category": "vendor", "kind": "asserts-same"},
            {"publisher": "B", "url": "https://b", "category": "vendor", "kind": "asserts-same"},
        ],
    }
    verdict = filter_truth(adjudication)
    assert verdict["admissible"] is True
    assert verdict["effective_truth"] == "same_actor"


def test_assess_combines_ach_grading_and_adjudication() -> None:
    document = {
        "question": "Did actor X compromise host Y?",
        "hypotheses": ["compromise", "benign"],
        "evidence": [
            {
                "id": "E1",
                "statement": "unique implant on host Y",
                "source": "telemetry",
                "type": "code",
                "consistency": {"compromise": "C", "benign": "I"},
            }
        ],
        "judgement": {"confidence": "high", "probability": "very_likely"},
        "adjudication": {
            "truth": "distinct",
            "standard": "independent-corroboration",
            "sources": [
                {"publisher": "A", "url": "https://a", "category": "community", "kind": "asserts-distinct"},
                {"publisher": "B", "url": "https://b", "category": "vendor", "kind": "asserts-distinct"},
            ],
        },
    }
    verdict = assess(document)
    assert verdict["ranking"][0] == "compromise"
    assert verdict["grade"]["confidence"] == "high"
    assert verdict["truth"]["admissible"] is True


def test_calibrate_scores_a_labelled_claim() -> None:
    cases = [
        {
            "id": "c1",
            "question": "?",
            "truth": "distinct",
            "judgement": {"confidence": "high"},
            "evidence": [
                {
                    "id": "E1",
                    "statement": "different code",
                    "source": "s",
                    "type": "code",
                    "consistency": {"same_actor": "I", "distinct_but_overlapping": "C"},
                }
            ],
        }
    ]
    summary = calibrate(cases)
    assert summary["metrics"]["total"] == 1
    assert summary["metrics"]["false_merge_rate"] == 0.0
