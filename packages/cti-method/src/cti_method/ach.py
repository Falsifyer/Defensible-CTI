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
from typing import Any

from cti_method.evidence import Consistency, Evidence
from cti_method.sources import attribute, registry


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


def _voice_key(item: Evidence, known: dict[str, Any]) -> str:
    """The voice one item represents, for ranking: a publisher, not a repeat.

    The registry is the same one the ceiling uses. Without it, the normalised source
    string is the voice. Two items from one voice contribute at most their strongest
    inconsistency, so restating a claim does not move the ranking.
    """
    key = attribute(item.source, item.source_id, known)
    if key.registered:
        entry = known.get(key.key)
        publisher = (entry.publisher if entry else "").strip().lower()
        return publisher or key.key
    return key.key


def inconsistency_scores(
    evidence: list[Evidence],
    hypotheses: Sequence[str] | None = None,
    sources: Sequence[Any] | None = None,
) -> dict[str, float]:
    """Weighted contradiction score per hypothesis, counting independent voices.

    The sum is over voices, not items: if one source restates a contradiction, it counts
    once (at its strongest weight). This is what ranks hypotheses; the raw count is for
    display. It mirrors :func:`cti_method.sources.independent_ids`, which the ceiling
    already uses.
    """
    labels = _labels(hypotheses)
    matrix = consistency_matrix(evidence, labels)
    known = registry(list(sources) if sources is not None else None)
    voices = {item.id: _voice_key(item, known) for item in evidence}
    weights = {item.id: item.weight for item in evidence}
    scores: dict[str, float] = {label: 0.0 for label in labels}
    for label in labels:
        per_voice: dict[str, float] = {}
        for evidence_id, row in matrix.items():
            if row[label] is Consistency.INCONSISTENT:
                voice = voices.get(evidence_id, evidence_id)
                per_voice[voice] = max(per_voice.get(voice, 0.0), weights.get(evidence_id, 1.0))
        scores[label] = sum(per_voice.values())
    return {label: round(score, 4) for label, score in scores.items()}


def least_inconsistent(
    evidence: list[Evidence],
    hypotheses: Sequence[str] | None = None,
    sources: Sequence[Any] | None = None,
) -> list[str]:
    """Rank hypotheses by least weighted inconsistency, most favoured first.

    The order is deterministic, but the first item is not a tie-breaker: use
    :func:`tied_at_top` before presenting one hypothesis as *the* favoured one.
    """
    labels = _labels(hypotheses)
    scores = inconsistency_scores(evidence, labels, sources)
    order = list(labels)
    # The raw count is display only: using it here would let a source that restates a
    # claim break a weighted tie, which is the manipulation the voice rule removes.
    return sorted(order, key=lambda label: (scores[label], order.index(label)))


def tied_at_top(
    evidence: list[Evidence],
    hypotheses: Sequence[str] | None = None,
    sources: Sequence[Any] | None = None,
) -> list[str]:
    """The hypotheses that share the best weighted score: the evidence does not separate them.

    A single-element list means there is a unique favourite; an empty list means there are
    no hypotheses. Never resolve a tie by the order in which the analyst wrote the labels.
    """
    labels = _labels(hypotheses)
    ranking = least_inconsistent(evidence, labels, sources)
    if not ranking:
        return []
    scores = inconsistency_scores(evidence, labels, sources)
    best = scores[ranking[0]]
    return [label for label in ranking if scores[label] == best]


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
