"""The shared core is a stable, importable surface for the whole family."""

from __future__ import annotations

import cryptonym.method as method


def test_the_facade_exposes_the_grading_axes() -> None:
    judgement = method.Judgement(confidence=method.Confidence.LOW, probability=method.Probability.VERY_LIKELY)
    assert judgement.is_two_axis()
    assert method.parse_confidence("high") is method.Confidence.HIGH


def test_the_facade_runs_a_minimal_assessment() -> None:
    assessment = method.Assessment(
        id="demo",
        question="Are A and B the same?",
        evidence=[
            method.Evidence(
                id="E1",
                statement="shared tradecraft",
                source="s",
                type=method.EvidenceType.TACTICS,
                consistency={"same_actor": method.Consistency.CONSISTENT},
            )
        ],
        judgement=method.Judgement(confidence=method.Confidence.LOW),
    )
    verdict = method.assess_actor_pair(assessment)
    assert verdict["hypotheses_favoured"][0] == "same_actor"


def test_the_facade_exposes_the_adjudication_filter() -> None:
    adjudication = method.Adjudication(
        truth=method.Truth.SAME_ACTOR,
        standard=method.Standard.VENDOR_CONSENSUS,
        sources=(
            method.Source("A", "https://a", method.SourceCategory.VENDOR, method.SourceKind.ASSERTS_SAME),
            method.Source("B", "https://b", method.SourceCategory.VENDOR, method.SourceKind.ASSERTS_SAME),
        ),
    )
    verdict = method.filter_adjudication(adjudication)
    assert verdict.admissible is True


def test_the_facade_exposes_reconciliation_and_provenance() -> None:
    reconciliation = method.Reconciliation(
        [method.Linkage("A", "B", method.Confidence.MODERATE, "x")]
    )
    assert any(len(cluster) == 2 for cluster in reconciliation.clusters(method.Confidence.MODERATE))
    snapshot = method.Snapshot.capture("https://a", "body")
    assert snapshot.verify()
