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
    evidence: list[Evidence],
    hypotheses: Sequence[str] | None = None,
    sources: Sequence[Any] | None = None,
) -> dict[str, int]:
    """Count, per hypothesis, how many independent voices contradict it.

    The raw item count is not used: one source restated twice would otherwise look like
    two contradictions. The weighted score is the ranking; this count is the visible
    second key and the display.
    """
    labels = _labels(hypotheses)
    matrix = consistency_matrix(evidence, labels)
    known = registry(list(sources) if sources is not None else None)
    voices = {item.id: _voice_key(item, known) for item in evidence}
    counts: Counter[str] = Counter()
    for label in labels:
        contradicting = {
            voices.get(evidence_id, evidence_id)
            for evidence_id, row in matrix.items()
            if row[label] is Consistency.INCONSISTENT
        }
        counts[label] = len(contradicting)
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


def addressed_hypotheses(
    evidence: list[Evidence], hypotheses: Sequence[str] | None = None
) -> set[str]:
    """Hypotheses at least one item addresses with a non-neutral consistency.

    A hypothesis no item addresses has no inconsistencies by construction. Without this
    guard it wins every tie by silence, which is the opposite of ACH: the alternatives must
    be tested, not merely left unmentioned.
    """
    labels = set(_labels(hypotheses))
    return {
        label
        for item in evidence
        for label, value in item.consistency.items()
        if label in labels and value is not Consistency.NEUTRAL
    }


def supported_hypotheses(
    evidence: list[Evidence], hypotheses: Sequence[str] | None = None
) -> set[str]:
    """Hypotheses with at least one **diagnostic** item consistent with them.

    ``addressed`` says the evidence mentions the hypothesis; ``supported`` says something
    that can bear on identity actually points at it. A hypothesis with only linguistic or
    structural consistency is addressed but unsupported, and cannot be the favourite of an
    identity question.
    """
    labels = set(_labels(hypotheses))
    return {
        label
        for item in evidence
        if item.diagnostic
        for label, value in item.consistency.items()
        if label in labels and value is Consistency.CONSISTENT
    }


def least_inconsistent(
    evidence: list[Evidence],
    hypotheses: Sequence[str] | None = None,
    sources: Sequence[Any] | None = None,
) -> list[str]:
    """Rank hypotheses by least weighted inconsistency, most favoured first.

    Addressed hypotheses come before unaddressed ones; the order is deterministic, but
    the first item is not a tie-breaker: use :func:`tied_at_top` before presenting one
    hypothesis as *the* favoured one.
    """
    labels = _labels(hypotheses)
    scores = inconsistency_scores(evidence, labels, sources)
    counts = inconsistency_counts(evidence, labels, sources)
    addressed = addressed_hypotheses(evidence, labels)
    supported = supported_hypotheses(evidence, labels)
    order = list(labels)
    # Addressed first, then actually supported; both keys count voices, so a source
    # restated twice cannot break a tie either.
    return sorted(
        order,
        key=lambda label: (
            label not in addressed,
            label not in supported,
            scores[label],
            counts[label],
            order.index(label),
        ),
    )


def tied_at_top(
    evidence: list[Evidence],
    hypotheses: Sequence[str] | None = None,
    sources: Sequence[Any] | None = None,
) -> list[str]:
    """The hypotheses that share the best (voice-weighted score, voice count).

    A single-element list means there is a unique favourite; an empty list means there are
    no hypotheses. Never resolve a tie by the order in which the analyst wrote the labels.
    """
    labels = _labels(hypotheses)
    ranking = least_inconsistent(evidence, labels, sources)
    if not ranking:
        return []
    scores = inconsistency_scores(evidence, labels, sources)
    counts = inconsistency_counts(evidence, labels, sources)
    addressed = addressed_hypotheses(evidence, labels)
    supported = supported_hypotheses(evidence, labels)
    best = (
        ranking[0] in addressed,
        ranking[0] in supported,
        scores[ranking[0]],
        counts[ranking[0]],
    )
    return [
        label
        for label in ranking
        if (label in addressed, label in supported, scores[label], counts[label]) == best
    ]


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
