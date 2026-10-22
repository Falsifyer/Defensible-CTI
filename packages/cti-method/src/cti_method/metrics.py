"""Confusion, error rates and calibration: the arithmetic of scoring a method.

Positive class is whatever the caller says it is (``same_actor`` for alias work). A
**false positive** is a false merge, the costly error; a false negative is a false split,
cheaper and visible. The two rates are reported separately because they trade off and
averaging them would hide the only number that matters.
"""

from __future__ import annotations

from dataclasses import dataclass

#: Evaluation splits. A method graded on the cases it was tuned against proves nothing,
#: so results are always reported per split and never averaged into one headline.
SPLITS = ("development", "held-out")


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
            "false_merge_rate": self.false_positive_rate,
            "false_split_rate": self.false_negative_rate,
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
