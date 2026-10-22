"""Analysis of Competing Hypotheses (Heuer), mechanised, taxonomy-free and weighted.

Unstructured comparison drifts toward the most recent or loudest source. ACH forces the
alternatives to be written down and tests each item of evidence against all of them at
once: the favoured hypothesis is the one with the **least inconsistent evidence**, not
the one with the most supporters.

Items are weighted by their Admiralty reliability band (`Evidence.weight`), so a `C3`
report does not move the ranking as much as an `A1` one. Without a band, every item weighs
the same, which is the old behaviour.

The engine accepts any hypothesis labels, so it grades an alias question, a targeting
question or any other claim. Two senses of "diagnostic" are kept apart: an item is
*discriminating* when it separates the hypotheses; it is *identity-supporting* when its
type can bear on identity at all.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence

from cti_method.evidence import Consistency, Evidence


def _labels(hypotheses: Sequence[str] | None) -> list[str]:
    """Normalise hypotheses to plain labels, so the engine is not tied to one taxonomy."""
    if hypotheses is None:
        return []
    return [getattr(hypothesis, "value", None) or str(hypothesis) for hypothesis in hypotheses]


def consistency_matrix(
    evidence: list[Evidence], hypotheses: Sequence[str] | None = None
) -> dict[str, dict[str, Consistency]]:
    """Return ``{evidence_id: {hypothesis_label: consistency}}``.

    A hypothesis an item does not address is neutral, not consistent: silence is not
    support.
    """
    labels = _labels(hypotheses)
    matrix: dict[str, dict[str, Consistency]] = {}
    for item in evidence:
        matrix[item.id] = {label: item.consistency.get(label, Consistency.NEUTRAL) for label in labels}
    return matrix


def inconsistency_counts(
    evidence: list[Evidence], hypotheses: Sequence[str] | None = None
) -> dict[str, int]:
    """Count, per hypothesis, how many items of evidence contradict it."""
    labels = _labels(hypotheses)
    matrix = consistency_matrix(evidence, labels)
    counts: Counter[str] = Counter()
    for row in matrix.values():
        for label in labels:
            if row[label] is Consistency.INCONSISTENT:
                counts[label] += 1
    return {label: counts[label] for label in labels}


def inconsistency_scores(
    evidence: list[Evidence], hypotheses: Sequence[str] | None = None
) -> dict[str, float]:
    """Weighted contradiction score per hypothesis: the sum of the weights of the items
    that contradict it. This is what ranks hypotheses; the raw count is for display."""
    labels = _labels(hypotheses)
    matrix = consistency_matrix(evidence, labels)
    weights = {item.id: item.weight for item in evidence}
    scores: dict[str, float] = {label: 0.0 for label in labels}
    for evidence_id, row in matrix.items():
        for label in labels:
            if row[label] is Consistency.INCONSISTENT:
                scores[label] += weights.get(evidence_id, 1.0)
    return {label: round(score, 4) for label, score in scores.items()}


def least_inconsistent(
    evidence: list[Evidence], hypotheses: Sequence[str] | None = None
) -> list[str]:
    """Rank hypotheses by least weighted inconsistency, most favoured first.

    Ties are broken by the raw count and then by hypothesis order, for determinism and
    not by strength of support.
    """
    labels = _labels(hypotheses)
    scores = inconsistency_scores(evidence, labels)
    counts = inconsistency_counts(evidence, labels)
    order = list(labels)
    return sorted(order, key=lambda label: (scores[label], counts[label], order.index(label)))


def discriminating_evidence(evidence: list[Evidence]) -> list[str]:
    """Ids of items that separate the hypotheses (ACH's sense of diagnostic)."""
    return [item.id for item in evidence if item.is_discriminating()]


def identity_supporting_evidence(evidence: list[Evidence]) -> list[str]:
    """Ids of items that both discriminate *and* can bear on identity by type.

    Usually a short list — often empty. That is the point: most of what looks like
    evidence of sameness cannot support an identity claim.
    """
    return [item.id for item in evidence if item.diagnostic and item.is_discriminating()]


def consistent_with_everything(evidence: list[Evidence]) -> list[str]:
    """Ids of items consistent with every hypothesis they address.

    These feel like evidence of sameness and are not. Shared tradecraft lives here, and
    the suite surfaces it so it is not mistaken for support.
    """
    return [item.id for item in evidence if not item.is_discriminating()]
