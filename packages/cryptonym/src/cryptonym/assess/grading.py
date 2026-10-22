"""Combine the consistency matrix with the derived grade into one reproducible judgement.

The judgement is not declared and then printed: the evidence sets a **ceiling**, the
dossier may declare a confidence at or below it, and a declaration above it is a high
finding. This is the rule that makes "two-axis confidence" a claim about evidence rather
than a text field.

The ceiling uses the dossier's source registry (independence is structural), weighs
evidence by its Admiralty band, and drops a step when the diagnostic evidence contradicts
the favoured hypothesis.
"""

from __future__ import annotations

from typing import Any

from cti_method.ach import (
    consistent_with_everything,
    discriminating_evidence,
    identity_supporting_evidence,
    inconsistency_counts,
    inconsistency_scores,
    least_inconsistent,
)
from cti_method.grading import check_declared, derived_grade

from cryptonym.model.assessment import Assessment


def assess_actor_pair(assessment: Assessment) -> dict[str, Any]:
    """Produce the machine-readable judgement for an assessment.

    The result is deliberately thin: it states the ranking, the weighted inconsistencies,
    what discriminates, what can actually bear on identity, the evidence-derived ceiling,
    the declared grade (if any) and the findings that say whether the declaration is allowed.
    """
    ranking = least_inconsistent(assessment.evidence, assessment.hypotheses)
    favoured = ranking[0] if ranking else None
    derived = derived_grade(assessment.evidence, assessment.sources, favoured)
    declared = assessment.judgement.confidence if assessment.declared else None
    findings = check_declared(declared, assessment.evidence, assessment.sources, favoured)
    return {
        "assessment_id": assessment.id,
        "version": assessment.version,
        "question": assessment.question,
        "requirement_id": assessment.requirement_id or None,
        "hypotheses_favoured": ranking,
        "inconsistencies": inconsistency_counts(assessment.evidence, assessment.hypotheses),
        "inconsistency_scores": inconsistency_scores(assessment.evidence, assessment.hypotheses),
        "discriminating_evidence": discriminating_evidence(assessment.evidence),
        "identity_supporting_evidence": identity_supporting_evidence(assessment.evidence),
        "consistent_with_everything": consistent_with_everything(assessment.evidence),
        "confidence": declared.value if declared is not None else None,
        "probability": assessment.judgement.probability.value
        if assessment.declared and assessment.judgement.probability is not None
        else None,
        "ceiling": derived["ceiling"],
        "grade_supported": not findings,
        "grade_findings": findings,
        "evidence_profile": derived["profile"],
        "grade_reasons": derived["reasons"],
        "review_trigger": assessment.review_trigger,
        "review_by": assessment.review_by or None,
        "gaps": list(assessment.gaps),
        "tlp": assessment.tlp,
    }
