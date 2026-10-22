"""Tests for evidence typing — the diagnostic / non-diagnostic distinction."""

from __future__ import annotations

from cryptonym.model.evidence import Consistency, Evidence, EvidenceType


def test_tactics_are_non_diagnostic() -> None:
    item = Evidence(id="E1", statement="same LOLBins", source="advisory", type=EvidenceType.TACTICS)
    assert item.diagnostic is False


def test_infrastructure_is_diagnostic() -> None:
    item = Evidence(id="E2", statement="shared C2", source="advisory", type=EvidenceType.INFRASTRUCTURE)
    assert item.diagnostic is True


def test_overlap_consistent_with_everything_does_not_discriminate() -> None:
    item = Evidence(
        id="E3",
        statement="shared tradecraft",
        source="advisory",
        type=EvidenceType.TACTICS,
        consistency={"same_actor": Consistency.CONSISTENT, "distinct_but_overlapping": Consistency.CONSISTENT},
    )
    assert item.is_discriminating() is False


def test_evidence_that_contradicts_a_hypothesis_discriminates() -> None:
    item = Evidence(
        id="E4",
        statement="vendors use overlap wording",
        source="advisory",
        type=EvidenceType.LINGUISTIC,
        consistency={"same_actor": Consistency.INCONSISTENT, "distinct_but_overlapping": Consistency.CONSISTENT},
    )
    assert item.is_discriminating() is True
