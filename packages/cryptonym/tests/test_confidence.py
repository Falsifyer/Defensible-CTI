"""Tests for two-axis grading."""

from __future__ import annotations

import pytest

from cryptonym.model.confidence import Confidence, Judgement, Probability, parse_confidence, parse_probability


def test_confidence_and_probability_are_independent() -> None:
    # A claim can be very likely at low confidence: the axes do not move together.
    judgement = Judgement(confidence=Confidence.LOW, probability=Probability.VERY_LIKELY)
    assert judgement.is_two_axis()
    assert "low" in judgement.label()
    assert "very_likely" in judgement.label()


def test_factual_claim_is_graded_on_confidence_only() -> None:
    judgement = Judgement(confidence=Confidence.HIGH)
    assert not judgement.is_two_axis()
    assert judgement.label() == "confidence: high"


def test_parse_confidence_is_case_insensitive() -> None:
    assert parse_confidence("MODERATE") is Confidence.MODERATE


def test_parse_confidence_rejects_unknown_value() -> None:
    with pytest.raises(ValueError, match="unknown confidence"):
        parse_confidence("certain")


def test_parse_probability_allows_none() -> None:
    assert parse_probability(None) is None


def test_parse_probability_rejects_unknown_value() -> None:
    with pytest.raises(ValueError, match="unknown probability"):
        parse_probability("probably")
