"""Two-axis grading: confidence and probability are independent and per claim.

**Confidence** is about the sourcing and the reasoning behind a judgement.
**Probability** is about how likely the estimated outcome is. They are not the same
thing, and a claim can be *very likely* at *low* confidence (a single source) or
*roughly even* at *high* confidence (strong data, genuine uncertainty). Conflating
them is the most common tradecraft error; keeping them apart is the point of this
module.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Confidence(StrEnum):
    """How good the sourcing and reasoning are for a claim."""

    HIGH = "high"  # corroborated by two or more independent authoritative sources
    MODERATE = "moderate"  # one credible source, or corroboration with gaps
    LOW = "low"  # single-source, self-claimed, or heavily inferential


class Probability(StrEnum):
    """How likely an estimative outcome is. Only used where the claim is estimative."""

    NEARLY_CERTAIN = "nearly_certain"
    VERY_LIKELY = "very_likely"
    LIKELY = "likely"
    ROUGHLY_EVEN = "roughly_even_chance"
    UNLIKELY = "unlikely"
    VERY_UNLIKELY = "very_unlikely"


@dataclass(frozen=True)
class Judgement:
    """A graded claim.

    ``probability`` is ``None`` for purely factual, non-estimative claims; those are
    graded on confidence alone. Where it is set, the claim is estimative and both
    axes stand.
    """

    confidence: Confidence
    probability: Probability | None = None
    probability_of: str | None = None

    def is_two_axis(self) -> bool:
        """True when both axes are stated (i.e. the claim is estimative)."""
        return self.probability is not None

    def label(self) -> str:
        text = f"confidence: {self.confidence.value}"
        if self.probability is not None:
            target = f" that {self.probability_of} is true" if self.probability_of else ""
            text += f"; probability{target}: {self.probability.value}"
        return text


def parse_confidence(value: str | Confidence) -> Confidence:
    if isinstance(value, Confidence):
        return value
    try:
        return Confidence(str(value).strip().lower())
    except ValueError as exc:
        allowed = ", ".join(item.value for item in Confidence)
        raise ValueError(f"unknown confidence {value!r}; expected one of: {allowed}") from exc


def parse_probability(value: str | Probability | None) -> Probability | None:
    if value is None or isinstance(value, Probability):
        return value
    try:
        return Probability(str(value).strip().lower())
    except ValueError as exc:
        allowed = ", ".join(item.value for item in Probability)
        raise ValueError(f"unknown probability {value!r}; expected one of: {allowed}") from exc
