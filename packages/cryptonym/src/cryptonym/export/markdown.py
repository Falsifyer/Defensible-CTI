"""Render an assessment as a reviewable markdown product.

This is the human artefact: the same shape an analyst would publish, carrying the
consistency matrix, which evidence actually discriminates, which of it can bear on
identity at all, and the intelligence gaps — so a reader can judge the work rather
than trust the conclusion.
"""

from __future__ import annotations

from cryptonym.assess.ach import (
    consistency_matrix,
    discriminating_evidence,
    identity_supporting_evidence,
    least_inconsistent,
)
from cryptonym.model.assessment import Assessment

_LEGEND = "`C` = consistent · `I` = inconsistent · `0` = neutral or ambiguous."


def render_assessment(assessment: Assessment) -> str:
    """Return the assessment as a markdown document."""
    hypotheses = assessment.hypotheses
    lines: list[str] = []
    lines.append(f"# {assessment.question}")
    lines.append("")
    lines.append("| | |")
    lines.append("|---|---|")
    lines.append("| **Product** | Assessment (structured technique: ACH) |")
    lines.append(f"| **Handling** | {assessment.tlp} — open sources only |")
    lines.append(f"| **Version** | {assessment.version} |")
    lines.append(f"| **Review trigger** | {assessment.review_trigger or 'n/a'} |")
    lines.append("")

    ranking = least_inconsistent(assessment.evidence, hypotheses)
    favoured = ranking[0] if ranking else "n/a"
    lines.append("## Bottom line")
    lines.append("")
    lines.append(
        f"Favoured hypothesis (least inconsistent evidence): **{favoured}** — "
        f"{assessment.judgement.label()}."
    )
    lines.append("")

    lines.append("## Evidence")
    lines.append("")
    lines.append("| # | Evidence | Source |")
    lines.append("|---|---|---|")
    for item in assessment.evidence:
        lines.append(f"| {item.id} | {item.statement} | {item.source} |")
    lines.append("")

    discriminating = discriminating_evidence(assessment.evidence)
    if discriminating:
        lines.append(f"**Discriminating evidence:** {', '.join(discriminating)}.")
    identity = identity_supporting_evidence(assessment.evidence)
    if identity:
        lines.append(f"**Identity-supporting evidence:** {', '.join(identity)}.")
    else:
        lines.append(
            "**Identity-supporting evidence:** none — the discriminating evidence is "
            "linguistic or structural, which cannot by itself sustain an identity claim."
        )
    lines.append("")

    lines.append("## Consistency matrix")
    lines.append("")
    lines.append(_LEGEND)
    lines.append("")
    lines.append("| Evidence | " + " | ".join(f"{h.code} ({h.value})" for h in hypotheses) + " |")
    lines.append("|" + "---|" * (len(hypotheses) + 1))
    matrix = consistency_matrix(assessment.evidence, hypotheses)
    for item in assessment.evidence:
        row = matrix[item.id]
        lines.append("| " + item.id + " | " + " | ".join(row[h.value].value for h in hypotheses) + " |")
    lines.append("")

    if assessment.gaps:
        lines.append("## Intelligence gaps")
        lines.append("")
        for gap in assessment.gaps:
            lines.append(f"- {gap}")
        lines.append("")

    if assessment.revisions:
        lines.append("## Revision history")
        lines.append("")
        lines.append("| Version | Date | Change |")
        lines.append("|---|---|---|")
        for revision in assessment.revisions:
            lines.append(f"| {revision.version} | {revision.date} | {revision.change} |")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
