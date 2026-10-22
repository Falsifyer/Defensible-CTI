"""Confusion, error rates and calibration for the reconciliation method.

Positive class is "the two designations are the same actor". A **false positive** is a
false merge (the costly error); a **false negative** is a false split (cheaper, and
visible). The rates are reported separately because they trade off against each other
and averaging them would hide the only number that matters.
"""

from __future__ import annotations

from dataclasses import dataclass

from cryptonym.assess.grading import assess_actor_pair
from cryptonym.config import SPLITS
from cryptonym.evaluate.adjudication import Adjudication, Truth, filter_adjudication
from cryptonym.model.assessment import Assessment, Hypothesis
from cryptonym.model.confidence import Confidence

POSITIVE = Hypothesis.SAME.value


@dataclass(frozen=True)
class Confusion:
    """Counts for the binary call "same actor" against the adjudicated truth."""

    true_positive: int = 0
    false_positive: int = 0
    true_negative: int = 0
    false_negative: int = 0

    @property
    def total(self) -> int:
        return self.true_positive + self.false_positive + self.true_negative + self.false_negative

    @property
    def false_merge_rate(self) -> float | None:
        """Share of genuinely distinct pairs wrongly called the same actor."""
        denominator = self.false_positive + self.true_negative
        return self.false_positive / denominator if denominator else None

    @property
    def false_split_rate(self) -> float | None:
        """Share of genuinely same pairs wrongly kept apart."""
        denominator = self.false_negative + self.true_positive
        return self.false_negative / denominator if denominator else None

    def as_dict(self) -> dict[str, int | float | None]:
        return {
            "true_positive": self.true_positive,
            "false_positive": self.false_positive,
            "true_negative": self.true_negative,
            "false_negative": self.false_negative,
            "total": self.total,
            "false_merge_rate": self.false_merge_rate,
            "false_split_rate": self.false_split_rate,
        }


def confusion_from_calls(calls: list[tuple[bool, bool]]) -> Confusion:
    """Build a :class:`Confusion` from ``(called_same, truth_same)`` pairs."""
    counts = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}
    for called_same, truth_same in calls:
        if called_same and truth_same:
            counts["tp"] += 1
        elif called_same and not truth_same:
            counts["fp"] += 1
        elif not called_same and truth_same:
            counts["fn"] += 1
        else:
            counts["tn"] += 1
    return Confusion(
        true_positive=counts["tp"],
        false_positive=counts["fp"],
        true_negative=counts["tn"],
        false_negative=counts["fn"],
    )


def calibration_table(records: list[tuple[str, bool]]) -> dict[str, dict[str, float | int]]:
    """Accuracy per confidence level, from ``(confidence_value, correct)`` records.

    A grading scheme that does not calibrate — high-confidence calls no more reliable
    than low-confidence ones — is decoration. This table is how that is checked.
    """
    buckets: dict[str, list[bool]] = {}
    for confidence, correct in records:
        buckets.setdefault(confidence, []).append(correct)
    table: dict[str, dict[str, float | int]] = {}
    for level in (Confidence.HIGH.value, Confidence.MODERATE.value, Confidence.LOW.value):
        outcomes = buckets.get(level)
        if outcomes:
            table[level] = {"n": len(outcomes), "accuracy": sum(outcomes) / len(outcomes)}
    return table


def evaluate_cases(cases: list[dict]) -> dict:
    """Run the engine over a labelled corpus and summarise the method.

    Each case carries its authored evidence plus an adjudicated ``truth``. The engine
    must re-derive the favourite hypothesis from the evidence; the harness then asks
    whether that favourite agrees with the truth, and at what confidence.
    """
    results: list[dict] = []
    for case in cases:
        assessment = Assessment.from_dict(case)
        verdict = assess_actor_pair(assessment)
        favourite = verdict["hypotheses_favoured"][0] if verdict["hypotheses_favoured"] else "n/a"
        called_same = favourite == POSITIVE
        truth_same = case["truth"] == POSITIVE
        results.append(
            {
                "id": case["id"],
                "truth": case["truth"],
                "favourite": favourite,
                "called_same": called_same,
                "correct": called_same == truth_same,
                "confidence": verdict["confidence"],
                "probability": verdict["probability"],
            }
        )
    confusion = confusion_from_calls([(row["called_same"], row["truth"] == POSITIVE) for row in results])
    calibration = calibration_table([(row["confidence"], row["correct"]) for row in results])
    return {"results": results, "metrics": confusion.as_dict(), "calibration": calibration}


def _summarise(cases: list[dict]) -> dict[str, dict]:
    result = evaluate_cases(cases)
    return {"metrics": result["metrics"], "calibration": result["calibration"]}


def evaluate_corpus(document: dict) -> dict:
    """Score a corpus, reported **per split** and overall.

    A method graded on the cases it was tuned against proves nothing, so the
    development and held-out splits are never averaged into one number: the held-out
    result is the one that counts.
    """
    cases = document.get("cases", [])
    splits: dict[str, dict[str, dict]] = {}
    for name in SPLITS:
        subset = [case for case in cases if case.get("split") == name]
        if subset:
            splits[name] = _summarise(subset)
    return {
        "overall": _summarise(cases),
        "splits": splits,
        "results": evaluate_cases(cases)["results"],
    }


def evaluate_adjudicated(document: dict) -> dict:
    """Score an adjudicated corpus: only cases whose truth is *admissible* count.

    Every case is run through the external-truth filter. Cases whose effective truth is
    ``same_actor`` or ``distinct`` enter the confusion matrix; ``contested`` and
    ``unadjudicated`` cases are reported as **coverage**, never folded into error rates.
    The coverage and standards tables are the honest headline: they say how much of the
    corpus actually met the bar for an external truth.
    """
    cases = document.get("cases", [])
    calls: list[tuple[bool, bool]] = []
    calibration_records: list[tuple[str, bool]] = []
    coverage = {"admissible": 0, "contested": 0, "unadjudicated": 0}
    by_standard: dict[str, int] = {}
    results: list[dict] = []

    for case in cases:
        adjudication = Adjudication.from_dict(case["adjudication"])
        verdict = filter_adjudication(adjudication)
        engine = assess_actor_pair(Assessment.from_dict(case))
        favourite = engine["hypotheses_favoured"][0] if engine["hypotheses_favoured"] else "n/a"
        called_same = favourite == POSITIVE

        correct: bool | None = None
        if verdict.effective_truth.is_binary:
            calls.append((called_same, verdict.effective_truth is Truth.SAME_ACTOR))
            correct = called_same == (verdict.effective_truth is Truth.SAME_ACTOR)
            calibration_records.append((engine["confidence"], correct))
            coverage["admissible"] += 1
        else:
            coverage[verdict.effective_truth.value] = coverage.get(verdict.effective_truth.value, 0) + 1

        if verdict.standard is not None:
            name = verdict.standard.name.lower().replace("_", "-")
            by_standard[name] = by_standard.get(name, 0) + 1

        results.append(
            {
                "id": case["id"],
                "declared_truth": verdict.declared_truth.value,
                "effective_truth": verdict.effective_truth.value,
                "admissible": verdict.admissible,
                "standard": verdict.standard.name.lower().replace("_", "-") if verdict.standard else None,
                "independent_sources": verdict.independent_sources,
                "favourite": favourite,
                "called_same": called_same,
                "correct": correct,
                "reasons": list(verdict.reasons),
            }
        )

    return {
        "metrics": confusion_from_calls(calls).as_dict(),
        "calibration": calibration_table(calibration_records),
        "coverage": coverage,
        "by_standard": by_standard,
        "results": results,
    }
