"""Tests for the markdown product."""

from __future__ import annotations

from cryptonym.export.markdown import render_assessment
from cryptonym.model.assessment import Assessment, Hypothesis
from cryptonym.model.confidence import Confidence, Judgement
from cryptonym.model.designation import Designation
from cryptonym.model.evidence import Consistency, Evidence, EvidenceType


def _assessment() -> Assessment:
    return Assessment(
        id="demo",
        question="Is A the same actor as B?",
        subjects=[Designation("VendorA", "A"), Designation("VendorB", "B")],
        evidence=[
            Evidence(
                id="E1",
                statement="shared tradecraft",
                source="advisory",
                type=EvidenceType.TACTICS,
                consistency={h.value: Consistency.CONSISTENT for h in Hypothesis},
            ),
            Evidence(
                id="E2",
                statement="vendor uses overlap wording",
                source="vendor",
                type=EvidenceType.LINGUISTIC,
                consistency={
                    Hypothesis.SAME.value: Consistency.INCONSISTENT,
                    Hypothesis.OVERLAPPING.value: Consistency.CONSISTENT,
                },
            ),
        ],
        judgement=Judgement(confidence=Confidence.MODERATE),
        review_trigger="a new advisory",
        gaps=["no shared-infrastructure analysis"],
        version="1.0",
    )


def test_render_includes_matrix_and_bottom_line() -> None:
    document = render_assessment(_assessment())
    assert "## Consistency matrix" in document
    assert "Is A the same actor as B?" in document
    assert "distinct_but_overlapping" in document
    assert "| E1 | C | C | C |" in document


def test_render_reports_gaps_and_discriminating_evidence() -> None:
    document = render_assessment(_assessment())
    assert "Discriminating evidence" in document
    assert "no shared-infrastructure analysis" in document


def test_render_flags_when_no_identity_supporting_evidence_exists() -> None:
    document = render_assessment(_assessment())
    assert "Identity-supporting evidence:** none" in document
