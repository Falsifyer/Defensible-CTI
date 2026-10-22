"""Traceability between the six artifacts.

The cycle is only a cycle if an artifact can name the one it answers. Every document in
the suite carries the identifiers of the steps before it:

``requirement_id`` (pir) → ``assessment_id`` (cryptonym/assessment) → ``hunt_id``
(huntplan) → ``product_id``/``report`` (stixforge).

The rule for a link is: **when the upstream artifact is supplied, the identifier is
verified against it, never trusted as text.** A downstream document that cites an
assessment the upstream file does not contain is a high finding, not a typo.
"""

from __future__ import annotations

from typing import Any

from cti_method.contract import HIGH, MEDIUM, finding

#: Field name a downstream document uses to point at each upstream kind.
LINK_FIELDS = {
    "pir": "requirement_id",
    "assessment": "assessment_id",
    "hunt": "hunt_id",
}


def id_of(document: dict[str, Any]) -> str | None:
    """The identifier an artifact offers to the next step."""
    for key in ("id", "assessment_id", "requirement_id", "hunt_id", "product_id"):
        value = document.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def requirement_ids(register: dict[str, Any]) -> list[str]:
    """Every requirement identifier a pir register declares."""
    return [
        str(item["id"])
        for item in register.get("requirements") or []
        if isinstance(item, dict) and item.get("id")
    ]


def link(downstream: dict[str, Any], field_name: str, upstream: dict[str, Any], *, label: str) -> dict[str, Any]:
    """Verify (or adopt) the identifier that points from ``downstream`` to ``upstream``.

    Returns ``{"id": <verified id or None>, "findings": [...]}``.
    """
    declared = downstream.get(field_name)
    declared = declared.strip() if isinstance(declared, str) and declared.strip() else None
    actual = id_of(upstream)
    findings: list[dict[str, str]] = []

    if actual is None:
        findings.append(
            finding(
                "trace-unidentified",
                MEDIUM,
                f"the {label} file has no id, so a link to it cannot be verified",
            )
        )
        return {"id": declared, "findings": findings}
    if declared and declared != actual:
        findings.append(
            finding(
                "trace-mismatch",
                HIGH,
                f"{field_name} is {declared!r} but the {label} file is {actual!r}",
            )
        )
        return {"id": declared, "findings": findings}
    return {"id": actual, "findings": findings}


def link_requirement(downstream: dict[str, Any], register: dict[str, Any]) -> dict[str, Any]:
    """Verify that a dossier answers a requirement that exists in the register."""
    declared = downstream.get("requirement_id")
    declared = declared.strip() if isinstance(declared, str) and declared.strip() else None
    known = requirement_ids(register)
    if not declared:
        return {
            "id": None,
            "findings": [finding("trace-missing", MEDIUM, "the dossier does not cite the requirement it answers")],
        }
    if declared not in known:
        return {
            "id": declared,
            "findings": [
                finding(
                    "trace-unknown-requirement",
                    HIGH,
                    f"requirement_id {declared!r} is not in the register ({', '.join(known) or 'empty'})",
                )
            ],
        }
    return {"id": declared, "findings": []}


def external_references(ids: dict[str, str | None]) -> list[dict[str, str]]:
    """STIX ``external_references`` entries for the trace ids, in cycle order."""
    references: list[dict[str, str]] = []
    for kind, value in ids.items():
        if not value:
            continue
        references.append({"source_name": f"cti-suite:{kind}", "external_id": str(value)})
    return references
