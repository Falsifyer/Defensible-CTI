"""Tests for the ACH engine."""

from __future__ import annotations

from cryptonym.assess.ach import (
    consistency_matrix,
    consistent_with_everything,
    discriminating_evidence,
    identity_supporting_evidence,
    inconsistency_counts,
    least_inconsistent,
)
from cryptonym.model.assessment import Hypothesis
from cryptonym.model.evidence import Consistency, Evidence, EvidenceType


def _evidence() -> list[Evidence]:
    return [
        Evidence(
            id="E1",
            statement="vendor wording",
            source="vendor",
            type=EvidenceType.LINGUISTIC,
            consistency={
                Hypothesis.SAME.value: Consistency.INCONSISTENT,
                Hypothesis.OVERLAPPING.value: Consistency.CONSISTENT,
            },
        ),
        Evidence(
            id="E2",
            statement="shared tradecraft",
            source="advisory",
            type=EvidenceType.TACTICS,
            consistency={h.value: Consistency.CONSISTENT for h in Hypothesis},
        ),
        Evidence(
            id="E3",
            statement="broker hands footholds onward",
            source="vendor",
            type=EvidenceType.INFRASTRUCTURE,
            consistency={
                Hypothesis.SAME.value: Consistency.INCONSISTENT,
                Hypothesis.BROKERED.value: Consistency.CONSISTENT,
            },
        ),
    ]


def test_missing_hypothesis_is_neutral_not_consistent() -> None:
    matrix = consistency_matrix(_evidence())
    # E1 does not address the brokered hypothesis: silence is neutral, not support.
    assert matrix["E1"][Hypothesis.BROKERED.value] is Consistency.NEUTRAL


def test_least_inconsistent_prefers_fewest_contradictions() -> None:
    ranking = least_inconsistent(_evidence())
    # E3 is the only diagnostic item, and it is consistent with the brokered hypothesis;
    # linguistic/structural consistency alone is not enough (Phase 1).
    assert ranking[0] is Hypothesis.BROKERED.value
    # E1 and E3 share the "vendor" source: one voice, one contradiction.
    assert inconsistency_counts(_evidence())[Hypothesis.SAME.value] == 1


def test_discriminating_and_consistent_are_partitioned() -> None:
    evidence = _evidence()
    # E1 and E3 separate the hypotheses; E2 is consistent with all of them.
    assert discriminating_evidence(evidence) == ["E1", "E3"]
    assert consistent_with_everything(evidence) == ["E2"]


def test_the_engine_accepts_arbitrary_hypothesis_labels() -> None:
    evidence = [
        Evidence(
            id="E1",
            statement="evidence for X",
            source="s",
            type=EvidenceType.CODE,
            consistency={"X": Consistency.CONSISTENT, "Y": Consistency.INCONSISTENT},
        )
    ]
    assert least_inconsistent(evidence, ["Y", "X"]) == ["X", "Y"]
    assert inconsistency_counts(evidence, ["X", "Y"]) == {"X": 0, "Y": 1}


def test_identity_supporting_is_narrower_than_discriminating() -> None:
    # E1 discriminates but is linguistic; only E3 (infrastructure) can bear on identity.
    assert identity_supporting_evidence(_evidence()) == ["E3"]
