"""Render an assessment as a reviewable markdown product.

This is the human artefact: the same shape an analyst would publish, carrying the
consistency matrix, which evidence actually discriminates, which of it can bear on
identity at all, and the intelligence gaps — so a reader can judge the work rather
than trust the conclusion.
"""

from __future__ import annotations

from cryptonym.assess.ach import (
    addressed_hypotheses,
    consistency_matrix,
    discriminating_evidence,
    identity_supporting_evidence,
    least_inconsistent,
    ranking_basis,
    supported_hypotheses,
    tied_at_top,
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

    ranking = least_inconsistent(assessment.evidence, hypotheses, assessment.sources)
    tied = tied_at_top(assessment.evidence, hypotheses, assessment.sources)
    supported = supported_hypotheses(assessment.evidence, hypotheses)
    addressed = addressed_hypotheses(assessment.evidence, hypotheses)
    lines.append("## Bottom line")
    lines.append("")
    if len(tied) > 1:
        lines.append(
            f"The evidence does not separate **{'**, **'.join(tied)}** — no single "
            f"favoured hypothesis — {assessment.judgement.label()}."
        )
    elif ranking and ranking[0] in supported:
        favoured = ranking[0]
        lines.append(
            f"Favoured hypothesis (least inconsistent evidence): **{favoured}** — "
            f"{assessment.judgement.label()}."
        )
    else:
        labels = [str(item) for item in hypotheses]
        unsupported = [label for label in labels if label in addressed and label not in supported]
        shown = ", ".join(unsupported) or "none"
        lines.append(
            f"No hypothesis has diagnostic support ({shown}): the evidence is consistent "
            f"but unsupported — {assessment.judgement.label()}."
        )
    if len(tied) > 1:
        lines.append(f"**Tied:** {', '.join(tied)}.")
        lines.append("**Abstained:** the evidence does not make a binary call.")
    elif not supported:
        lines.append("**Abstained:** no hypothesis has diagnostic support.")
    if supported:
        lines.append(f"**Supported:** {', '.join(sorted(supported))}.")
    if addressed:
        unsupported = sorted(
            label for label in addressed if label not in supported
        )
        if unsupported:
            lines.append(
                f"**Addressed but unsupported:** {', '.join(unsupported)} "
                "(linguistic/structural only)."
            )
    lines.append("")

    basis = ranking_basis(assessment.evidence, hypotheses, assessment.sources)
    lines.append("## Ranking basis")
    lines.append("")
    lines.append(f"Rule: {basis['rule']}.")
    lines.append("")
    lines.append("| Hypothesis | Addressed | Supported | Identity I | Context I | Voices |")
    lines.append("|---|---|---|---|---|---|")
    for label, data in basis["hypotheses"].items():
        lines.append(
            f"| {label} | {'yes' if data['addressed'] else 'no'} "
            f"| {'yes' if data['supported'] else 'no'} "
            f"| {data['identity_inconsistency']} | {data['context_inconsistency']} "
            f"| {data['voices']} |"
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
