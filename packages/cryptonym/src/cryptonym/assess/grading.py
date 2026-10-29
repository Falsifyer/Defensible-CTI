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
    addressed_hypotheses,
    consistent_with_everything,
    discriminating_evidence,
    identity_supporting_evidence,
    inconsistency_counts,
    inconsistency_scores,
    least_inconsistent,
    ranking_basis,
    supported_hypotheses,
    tied_at_top,
)
from cti_method.grading import check_declared, derived_grade

from cryptonym.model.assessment import Assessment

_CEILING_RANK = {"low": 0, "moderate": 1, "high": 2}


def assess_actor_pair(assessment: Assessment) -> dict[str, Any]:
    """Produce the machine-readable judgement for an assessment.

    The result is deliberately thin: it states the ranking, the weighted inconsistencies,
    what discriminates, what can actually bear on identity, the evidence-derived ceiling,
    the declared grade (if any) and the findings that say whether the declaration is allowed.
    """
    ranking = least_inconsistent(assessment.evidence, assessment.hypotheses, assessment.sources)
    tied = tied_at_top(assessment.evidence, assessment.hypotheses, assessment.sources)
    tied = tied if len(tied) > 1 else []
    supported = supported_hypotheses(assessment.evidence, assessment.hypotheses)
    addressed = addressed_hypotheses(assessment.evidence, assessment.hypotheses)
    labels = [str(item) for item in assessment.hypotheses]
    favoured = (
        None
        if len(tied) > 1
        else (ranking[0] if ranking and ranking[0] in supported else None)
    )
    if len(tied) > 1:
        candidates = list(tied)
    elif favoured is not None:
        candidates = [favoured]
    else:
        candidates = []
    derived_candidates = [
        derived_grade(assessment.evidence, assessment.sources, label) for label in candidates
    ]
    if derived_candidates:
        derived = min(derived_candidates, key=lambda item: _CEILING_RANK[item["ceiling"]])
    else:
        derived = derived_grade(assessment.evidence, assessment.sources, favoured)
    if len(tied) > 1:
        derived = dict(derived)
        derived["reasons"] = [
            f"tied at the top: {', '.join(tied)}; the ceiling is the most restrictive of the "
            "tied hypotheses",
            *derived["reasons"],
        ]
    declared = assessment.judgement.confidence if assessment.declared else None
    findings: list[dict[str, str]] = []
    labels_to_check = candidates if candidates else ([favoured] if favoured is not None else [])
    for label in labels_to_check:
        findings.extend(
            check_declared(declared, assessment.evidence, assessment.sources, label)
        )
    unique: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for item in findings:
        key = (item["code"], item["message"])
        if key not in seen:
            seen.add(key)
            unique.append(item)
    findings = unique
    return {
        "assessment_id": assessment.id,
        "version": assessment.version,
        "question": assessment.question,
        "requirement_id": assessment.requirement_id or None,
        "hypotheses_favoured": ranking,
        "favoured": favoured,
        "tied": tied,
        "addressed": sorted(addressed),
        "supported": sorted(supported),
        "unsupported": [label for label in labels if label not in supported],
        "consistent_but_unsupported": [
            label for label in labels if label in addressed and label not in supported
        ],
        "inconsistencies": inconsistency_counts(
            assessment.evidence, assessment.hypotheses, assessment.sources
        ),
        "inconsistency_scores": inconsistency_scores(
            assessment.evidence, assessment.hypotheses, assessment.sources
        ),
        "identity_inconsistency_scores": inconsistency_scores(
            assessment.evidence, assessment.hypotheses, assessment.sources, scope="identity"
        ),
        "context_inconsistency_scores": inconsistency_scores(
            assessment.evidence, assessment.hypotheses, assessment.sources, scope="context"
        ),
        "ranking_basis": ranking_basis(
            assessment.evidence, assessment.hypotheses, assessment.sources
        ),
        "discriminating_evidence": discriminating_evidence(assessment.evidence),
        "identity_supporting_evidence": identity_supporting_evidence(assessment.evidence),
        "consistent_with_everything": consistent_with_everything(assessment.evidence),
        "confidence": declared.value if declared is not None else None,
        "probability": assessment.judgement.probability.value
        if assessment.declared and assessment.judgement.probability is not None
        else None,
        "probability_of": assessment.judgement.probability_of,
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
