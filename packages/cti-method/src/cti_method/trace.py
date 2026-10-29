"""Traceability between the six artifacts.

The cycle is only a cycle if an artifact can name the one it answers. Every document in
the suite carries the identifiers of the steps before it:

``requirement_id`` (pir) → ``assessment_id`` (cryptonym/assessment) → ``hunt_id``
(huntplan) → ``product_id``/``report`` (stixforge).

The rule for a link is: **when the upstream artifact is supplied, the identifier is
verified against it, never trusted as text.** A downstream document that cites an
assessment the upstream file does not contain is a high finding, not a typo.

An identifier alone is not enough: an edited dossier keeps its id. When the downstream
document also records ``<kind>_hash``, the hash of the exact upstream content is verified
and travels in the STIX reference as ``<id>@<sha256>``.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from cti_method.contract import HIGH, MEDIUM, finding

#: Field name a downstream document uses to point at each upstream kind.
LINK_FIELDS = {
    "pir": "requirement_id",
    "assessment": "assessment_id",
    "hunt": "hunt_id",
    "product": "product_id",
}

#: Where each kind keeps its identifier. Explicit per kind: guessing an id by trying keys
#: in order picks the wrong one as soon as a document has more than one.
_ID_FIELDS: dict[str, tuple[str, ...]] = {
    "pir": ("requirement_id", "id"),
    "assessment": ("assessment_id", "id"),
    "hunt": ("hunt_id", "id"),
    "product": ("product_id", "id"),
}


def id_of(document: dict[str, Any], kind: str | None = None) -> str | None:
    """The identifier an artifact offers to the next step, read from the field for its kind."""
    if kind is None:
        raise TypeError("id_of needs the artifact kind: an id guessed from several fields is a bug")
    for field_name in _ID_FIELDS.get(kind, ("id",)):
        value = document.get(field_name)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def content_hash(document: Any) -> str:
    """SHA-256 of the canonical JSON of a document, for pinning the exact content."""
    canonical = json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def hash_field(field_name: str) -> str:
    """``assessment_id`` -> ``assessment_hash``."""
    return field_name.removesuffix("_id") + "_hash"


def requirement_ids(register: dict[str, Any]) -> list[str]:
    """Every requirement identifier a pir register declares."""
    return [
        str(item["id"])
        for item in register.get("requirements") or []
        if isinstance(item, dict) and item.get("id")
    ]


def link(
    downstream: dict[str, Any],
    field_name: str,
    upstream: dict[str, Any],
    *,
    label: str,
    kind: str | None = None,
) -> dict[str, Any]:
    """Verify (or adopt) the identifier and the optional hash that point at ``upstream``.

    Returns ``{"id": <verified id or None>, "hash": <sha256 or None>, "findings": [...]}``.
    """
    declared = downstream.get(field_name)
    declared = declared.strip() if isinstance(declared, str) and declared.strip() else None
    actual = id_of(upstream, kind)
    actual_hash = content_hash(upstream)
    findings: list[dict[str, str]] = []

    if actual is None:
        findings.append(
            finding(
                "trace-unidentified",
                MEDIUM,
                f"the {label} file has no id, so a link to it cannot be verified",
            )
        )
        return {"id": declared, "hash": actual_hash, "findings": findings}
    if declared and declared != actual:
        findings.append(
            finding(
                "trace-mismatch",
                HIGH,
                f"{field_name} is {declared!r} but the {label} file is {actual!r}",
            )
        )
        return {"id": declared, "hash": actual_hash, "findings": findings}

    declared_hash = downstream.get(hash_field(field_name))
    if isinstance(declared_hash, str) and declared_hash.strip():
        if declared_hash.strip().lower() != actual_hash:
            findings.append(
                finding(
                    "trace-hash-mismatch",
                    HIGH,
                    f"{hash_field(field_name)} is {declared_hash.strip()[:12]}… but the {label} "
                    f"content hashes to {actual_hash[:12]}…: the upstream document changed after "
                    "this one was written",
                )
            )
    return {"id": actual, "hash": actual_hash, "findings": findings}


def link_requirement(downstream: dict[str, Any], register: dict[str, Any]) -> dict[str, Any]:
    """Verify that a dossier answers a requirement that exists in the register."""
    declared = downstream.get("requirement_id")
    declared = declared.strip() if isinstance(declared, str) and declared.strip() else None
    known = requirement_ids(register)
    if not declared:
        return {
            "id": None,
            "hash": content_hash(register),
            "findings": [finding("trace-missing", MEDIUM, "the dossier does not cite the requirement it answers")],
        }
    if declared not in known:
        return {
            "id": declared,
            "hash": content_hash(register),
            "findings": [
                finding(
                    "trace-unknown-requirement",
                    HIGH,
                    f"requirement_id {declared!r} is not in the register ({', '.join(known) or 'empty'})",
                )
            ],
        }
    return {"id": declared, "hash": content_hash(register), "findings": []}


def external_references(
    ids: dict[str, str | None], hashes: dict[str, str | None] | None = None
) -> list[dict[str, str]]:
    """STIX ``external_references`` entries for the trace, in cycle order.

    With a hash, the reference is ``<id>@<sha256>``: a consumer can tell that the
    judgement it is reading is the one the bundle was built from.
    """
    references: list[dict[str, str]] = []
    for kind, value in ids.items():
        if not value:
            continue
        external_id = str(value)
        digest = (hashes or {}).get(kind)
        if digest:
            external_id = f"{external_id}@{digest}"
        references.append({"source_name": f"cti-suite:{kind}", "external_id": external_id})
    return references
