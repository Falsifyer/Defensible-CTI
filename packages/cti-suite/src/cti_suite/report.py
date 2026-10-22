"""The one artifact a consumer reads: the whole cycle as markdown.

Six tools produce six JSON documents. Nobody outside the team reads six JSON documents.
This module renders one product — requirement, judgement, evidence, what would break it,
hunt plan and marking — from the artifacts the chain already produced, and it refuses to
invent anything that is not in them.
"""

from __future__ import annotations

from typing import Any

_LABEL = {"high": "high", "moderate": "moderate", "low": "low"}


def _row(cells: list[Any]) -> str:
    return "| " + " | ".join(str(cell) if cell not in (None, "") else "—" for cell in cells) + " |"


def _requirement_heading(pir: dict[str, Any] | None, requirement_id: str | None) -> list[str]:
    if not pir:
        return []
    requirements = pir.get("requirements") or []
    selected = [item for item in requirements if not requirement_id or item.get("id") == requirement_id]
    if not selected:
        return [f"**Requirement `{requirement_id}` not found in the register.**", ""]
    lines = ["## Requirement", ""]
    for item in selected:
        lines.append(f"**{item.get('id', '?')} — {item.get('question', '')}**")
        lines.append("")
        lines.append(f"- Decision it informs: {item.get('decision', '—')}")
        lines.append(f"- Consumer: {item.get('consumer', '—')}")
        lines.append(
            f"- Priority: {item.get('priority', '—')} · deadline: {item.get('deadline', '—')}"
            f" · status: {item.get('status', 'open')}"
        )
        for eei in item.get("eei") or []:
            lines.append(f"- EEI {eei.get('id', '')}: {eei.get('question', '')}")
            for indicator in eei.get("indicators") or []:
                lines.append(f"  - {indicator.get('value', '')} (source {indicator.get('source', '—')})")
        lines.append("")
    return lines


def _judgement(assessment: dict[str, Any] | None) -> list[str]:
    if not assessment:
        return []
    ranking = assessment.get("hypotheses_favoured") or assessment.get("ranking") or []
    grade = assessment.get("grade") or {}
    confidence = grade.get("confidence", assessment.get("confidence"))
    ceiling = assessment.get("ceiling")
    lines = [
        "## Judgement",
        "",
        f"**Favoured: {ranking[0] if ranking else '—'}** — declared confidence: "
        f"{_LABEL.get(str(confidence), confidence) if confidence else 'none'}; "
        f"the evidence supports at most **{ceiling or '—'}**.",
        "",
        "| Hypothesis | Inconsistencies |",
        "|---|---|",
    ]
    for label, count in (assessment.get("inconsistencies") or {}).items():
        lines.append(_row([label, count]))
    lines.append("")
    if ranking:
        lines.append(f"Ranking (least inconsistent first): {', '.join(ranking)}")
        lines.append("")
    discriminating = assessment.get("discriminating_evidence") or []
    weak = assessment.get("consistent_with_everything") or []
    lines.append(f"- Evidence that discriminates: {', '.join(discriminating) if discriminating else 'none'}")
    lines.append(
        f"- Evidence consistent with everything (not support): {', '.join(weak) if weak else 'none'}"
    )
    if assessment.get("review_trigger"):
        lines.append(f"- What would change the judgement: {assessment['review_trigger']}")
    if assessment.get("review_by"):
        lines.append(f"- Review by: {assessment['review_by']}")
    for gap in assessment.get("gaps") or []:
        lines.append(f"- Gap: {gap}")
    lines.append("")
    return lines


def _evidence_table(assessment: dict[str, Any] | None) -> list[str]:
    evidence = (assessment or {}).get("evidence") or []
    if not evidence:
        return []
    lines = ["## Evidence", "", "| Id | Type | Source | Consistency |", "|---|---|---|---|"]
    for item in evidence:
        consistency = ", ".join(f"{key}={value}" for key, value in (item.get("consistency") or {}).items())
        lines.append(_row([item.get("id"), item.get("type"), item.get("source"), consistency]))
    lines.append("")
    return lines


def _hunt(hunt: dict[str, Any] | None) -> list[str]:
    if not hunt:
        return []
    lines = ["## Hunt plan", "", f"**{hunt.get('id') or 'Hunt'} — {hunt.get('question') or ''}**", ""]
    lines.append(f"- Hypothesis: {hunt.get('hypothesis', '—')}")
    lines.append(f"- Closure: {hunt.get('closure', '—')}")
    for technique in hunt.get("techniques") or []:
        strategies = technique.get("detection_strategies") or []
        names = ", ".join(strategy.get("id", "") for strategy in strategies) or "none in the curated subset"
        lines.append(
            f"- {technique.get('technique_id')} {technique.get('technique') or ''} — detection strategies: {names}"
        )
        components = technique.get("data_components") or []
        if components:
            lines.append(f"  - Data components: {', '.join(components[:8])}")
    attack = hunt.get("attack") or {}
    if attack:
        lines.append(
            f"- ATT&CK: {attack.get('collection')} {attack.get('attack_version')}"
            f" (modified {attack.get('collection_modified')})"
        )
    lines.append("")
    return lines


def _product(product: dict[str, Any] | None, bundle: dict[str, Any] | None, marking: str | None) -> list[str]:
    if not product and not bundle:
        return []
    lines = ["## Product", ""]
    if product:
        lines.append(f"- Id: {product.get('id', '—')} · title: {product.get('title', '—')}")
        lines.append(f"- Author: {product.get('author', '—')}")
    if marking:
        lines.append(f"- TLP: **{marking}**")
    if bundle:
        types: dict[str, int] = {}
        for obj in bundle.get("objects") or []:
            types[obj.get("type", "?")] = types.get(obj.get("type", "?"), 0) + 1
        counts = ", ".join(f"{key} ×{value}" for key, value in sorted(types.items()))
        lines.append(f"- Bundle: {len(bundle.get('objects') or [])} objects — {counts}")
        report = next((obj for obj in bundle.get("objects") or [] if obj.get("type") == "report"), None)
        references = (report or {}).get("external_references") or []
        if references:
            lines.append("- Trace: " + ", ".join(f"{item['source_name']}={item['external_id']}" for item in references))
    lines.append("")
    return lines


def render_report(
    *,
    pir: dict[str, Any] | None = None,
    assessment: dict[str, Any] | None = None,
    hunt: dict[str, Any] | None = None,
    product: dict[str, Any] | None = None,
    bundle: dict[str, Any] | None = None,
    marking: str | None = None,
) -> str:
    """Render the product. Nothing here is computed that the inputs do not contain."""
    requirement_id = (assessment or {}).get("requirement_id")
    title = (product or {}).get("title") or (assessment or {}).get("question") or "Intelligence product"
    header = [f"# {title}", ""]
    if marking:
        header.append(f"> {marking}")
        header.append("")
    body: list[str] = []
    body += _requirement_heading(pir, requirement_id)
    body += _judgement(assessment)
    body += _evidence_table(assessment)
    body += _hunt(hunt)
    body += _product(product, bundle, marking)

    missing = [
        name
        for name, value in (
            ("requirement register", pir),
            ("assessment", assessment),
            ("hunt plan", hunt),
            ("product", product or bundle),
        )
        if not value
    ]
    if missing:
        body += ["## What this product does not contain", ""]
        for name in missing:
            body.append(f"- No {name} was supplied: the chain is incomplete.")
        body.append("")
    return "\n".join(header + body).rstrip() + "\n"
