"""Tests for the evaluation metrics."""

from __future__ import annotations

from cryptonym.evaluate.metrics import (
    Confusion,
    calibration_table,
    confusion_from_calls,
    evaluate_cases,
    evaluate_corpus,
)


def test_confusion_counts_each_outcome() -> None:
    confusion = confusion_from_calls([(True, True), (True, False), (False, True), (False, False)])
    assert (confusion.true_positive, confusion.false_positive) == (1, 1)
    assert (confusion.true_negative, confusion.false_negative) == (1, 1)
    assert confusion.total == 4


def test_false_merge_rate_targets_the_costly_error() -> None:
    confusion = Confusion(true_positive=2, false_positive=1, true_negative=3, false_negative=0)
    assert confusion.false_merge_rate == 0.25  # 1 of 4 distinct pairs wrongly merged
    assert confusion.false_split_rate == 0.0


def test_rates_are_none_when_the_denominator_is_empty() -> None:
    confusion = Confusion()
    assert confusion.false_merge_rate is None
    assert confusion.false_split_rate is None


def test_calibration_reports_accuracy_per_level() -> None:
    table = calibration_table([("high", True), ("high", True), ("low", True), ("low", False)])
    assert table["high"]["accuracy"] == 1.0
    assert table["low"]["accuracy"] == 0.5
    assert table["low"]["n"] == 2


def test_evaluate_cases_derives_the_favourite_from_evidence() -> None:
    cases = [
        {
            "id": "distinct",
            "question": "same?",
            "truth": "distinct_but_overlapping",
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
        },
        {
            "id": "same",
            "question": "same?",
            "truth": "same_actor",
            "judgement": {"confidence": "high"},
            "evidence": [
                {
                    "id": "E1",
                    "statement": "shared tradecraft",
                    "source": "s",
                    "type": "tactics",
                    "consistency": {"same_actor": "C"},
                }
            ],
        },
    ]
    summary = evaluate_cases(cases)
    assert summary["metrics"]["false_merge_rate"] == 0.0
    assert summary["metrics"]["false_split_rate"] == 0.0
    # La calibracion se mide sobre el techo que fija la evidencia, no sobre el grado
    # declarado: un solo item diagnostico de una sola fuente no pasa de moderate.
    assert summary["calibration"]["moderate"]["accuracy"] == 1.0
    assert "high" not in summary["calibration"]


def test_evaluate_corpus_reports_each_split_separately() -> None:
    case = {
        "id": "x",
        "question": "same?",
        "truth": "distinct_but_overlapping",
        "split": "held-out",
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
    summary = evaluate_corpus({"cases": [case]})
    assert set(summary["splits"]) == {"held-out"}
    assert summary["overall"]["metrics"]["total"] == 1
    assert summary["splits"]["held-out"]["metrics"]["total"] == 1
