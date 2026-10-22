"""Confusion, error rates, confidence calibration and probability scoring.

Positive class is whatever the caller says it is (``same_actor`` for alias work). A
**false positive** is a false merge, the costly error; a false negative is a false split,
cheaper and visible. The two rates are reported separately because they trade off and
averaging them would hide the only number that matters.

The two axes of a judgement are scored separately, because they answer different questions:

* **confidence calibration** — when the evidence ceiling says ``high``, how often is the
  call right? (``calibration_table``)
* **probability calibration** — when the estimate says ``likely``, how often does it
  happen? (``probability_calibration``, with a Brier score)
"""

from __future__ import annotations

from dataclasses import dataclass

#: Evaluation splits. A method graded on the cases it was tuned against proves nothing,
#: so results are always reported per split and never averaged into one headline.
SPLITS = ("development", "held-out")

#: WEP-style probability bands mapped to the midpoint of the range they describe. The
#: bands are the ones the suite emits; the points are what a Brier score can use.
PROBABILITY_POINTS: dict[str, float] = {
    "nearly_certain": 0.95,
    "very_likely": 0.80,
    "likely": 0.65,
    "roughly_even_chance": 0.50,
    "unlikely": 0.35,
    "very_unlikely": 0.20,
}


@dataclass(frozen=True)
class Confusion:
    """Counts for the binary call against the adjudicated truth."""

    true_positive: int = 0
    false_positive: int = 0
    true_negative: int = 0
    false_negative: int = 0

    @property
    def total(self) -> int:
        return self.true_positive + self.false_positive + self.true_negative + self.false_negative

    @property
    def false_merge_rate(self) -> float | None:
        """Alias for the alias-reconciliation domain: a false positive is a false merge."""
        return self.false_positive_rate

    @property
    def false_split_rate(self) -> float | None:
        """Alias for the alias-reconciliation domain."""
        return self.false_negative_rate

    @property
    def false_positive_rate(self) -> float | None:
        denominator = self.false_positive + self.true_negative
        return self.false_positive / denominator if denominator else None

    @property
    def false_negative_rate(self) -> float | None:
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
    """Build a :class:`Confusion` from ``(called_positive, truth_positive)`` pairs."""
    counts = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}
    for called_positive, truth_positive in calls:
        if called_positive and truth_positive:
            counts["tp"] += 1
        elif called_positive and not truth_positive:
            counts["fp"] += 1
        elif not called_positive and truth_positive:
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
    for level in ("high", "moderate", "low"):
        outcomes = buckets.get(level)
        if outcomes:
            table[level] = {"n": len(outcomes), "accuracy": sum(outcomes) / len(outcomes)}
    return table


def probability_calibration(records: list[tuple[str | None, bool]]) -> dict[str, object]:
    """Brier score and per-band reliability for estimative calls.

    Each record is ``(probability_label, happened)``. Records with no probability are not
    estimative and are excluded — they have nothing to score on this axis.

    The Brier score is the mean squared error of the forecast: ``0`` is a perfect
    forecast, ``0.25`` is what always saying "50/50" scores, and a method that never beats
    that is not adding information.
    """
    usable: list[tuple[str, float, bool]] = []
    for label, happened in records:
        if not label:
            continue
        point = PROBABILITY_POINTS.get(str(label))
        if point is None:
            continue
        usable.append((str(label), point, bool(happened)))

    if not usable:
        return {"n": 0, "brier_score": None, "buckets": {}, "points": dict(PROBABILITY_POINTS)}

    differences = [(point - (1.0 if happened else 0.0)) ** 2 for _, point, happened in usable]
    buckets: dict[str, list[tuple[float, bool]]] = {}
    for label, point, happened in usable:
        buckets.setdefault(label, []).append((point, happened))
    table = {
        label: {
            "n": len(values),
            "mean_forecast": round(sum(point for point, _ in values) / len(values), 4),
            "observed_rate": round(sum(1 for _, happened in values if happened) / len(values), 4),
        }
        for label, values in sorted(buckets.items(), key=lambda item: -PROBABILITY_POINTS[item[0]])
    }
    return {
        "n": len(usable),
        "brier_score": round(sum(differences) / len(differences), 4),
        "buckets": table,
        "points": dict(PROBABILITY_POINTS),
    }
