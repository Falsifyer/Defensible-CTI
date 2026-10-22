"""Combine the consistency matrix with two-axis grading into one reproducible judgement."""

from __future__ import annotations

from typing import Any

from cryptonym.assess.ach import (
    consistent_with_everything,
    discriminating_evidence,
    identity_supporting_evidence,
    inconsistency_counts,
    least_inconsistent,
)
from cryptonym.model.assessment import Assessment


def assess_actor_pair(assessment: Assessment) -> dict[str, Any]:
    """Produce the machine-readable judgement for an assessment.

    The result is deliberately thin: it states the ranking, the inconsistencies, what
    discriminates, what can actually bear on identity, and the assessment's own
    two-axis grade — nothing it cannot cite.
    """
    ranking = least_inconsistent(assessment.evidence, assessment.hypotheses)
    return {
        "assessment_id": assessment.id,
        "version": assessment.version,
        "question": assessment.question,
        "hypotheses_favoured": ranking,
        "inconsistencies": inconsistency_counts(assessment.evidence, assessment.hypotheses),
        "discriminating_evidence": discriminating_evidence(assessment.evidence),
        "identity_supporting_evidence": identity_supporting_evidence(assessment.evidence),
        "consistent_with_everything": consistent_with_everything(assessment.evidence),
        "confidence": assessment.judgement.confidence.value,
        "probability": assessment.judgement.probability.value
        if assessment.judgement.probability is not None
        else None,
        "review_trigger": assessment.review_trigger,
        "gaps": list(assessment.gaps),
        "tlp": assessment.tlp,
    }
