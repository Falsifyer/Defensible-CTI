"""The gate itself: TLP correctness and STIX 2.1 conformance.

Ground truth is external and citable: the FIRST **TLP 2.0** definitions and the **STIX
2.1** specification. Nothing here is a judgement call, which is the point — a compliance
gate earns trust by being objective.
"""

from __future__ import annotations

import json
import re
from typing import Any

#: FIRST TLP 2.0. ``WHITE`` is the deprecated v1.0 marking for ``CLEAR``.
TLP: dict[str, dict[str, Any]] = {
    "RED": {
        "rank": 5,
        "summary": "Personal, eyes only. No disclosure beyond named recipients.",
    },
    "AMBER+STRICT": {
        "rank": 4,
        "summary": "Limited disclosure, restricted to the recipient's own organisation.",
    },
    "AMBER": {
        "rank": 3,
        "summary": "Limited disclosure, organisation plus clients on a need-to-know basis.",
    },
    "GREEN": {
        "rank": 2,
        "summary": "Limited disclosure, community-wide (peers and partners), not public.",
    },
    "CLEAR": {
        "rank": 1,
        "summary": "Unlimited disclosure; may be shared publicly.",
    },
    "WHITE": {
        "rank": 1,
        "summary": "Deprecated (TLP 1.0). Use TLP:CLEAR.",
        "deprecated": True,
    },
}

_TLP_RE = re.compile(r"TLP\s*:\s*(RED|AMBER\+STRICT|AMBER|GREEN|CLEAR|WHITE)", re.IGNORECASE)
_IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_SENSITIVE_RE = re.compile(
    r"\b(victim|compromised|credentials?|passwords?|confidential|internal use|need[- ]to[- ]know|attribution)\b",
    re.IGNORECASE,
)

HIGH, MEDIUM, LOW = "high", "medium", "low"


def _finding(code: str, severity: str, message: str, pointer: str | None = None) -> dict[str, str]:
    finding = {"code": code, "severity": severity, "message": message}
    if pointer:
        finding["pointer"] = pointer
    return finding


def _severity_counts(findings: list[dict[str, str]]) -> dict[str, int]:
    return {level: sum(1 for finding in findings if finding["severity"] == level) for level in (HIGH, MEDIUM, LOW)}


def _sensitive_categories(text: str) -> list[str]:
    categories = []
    if _IPV4_RE.search(text):
        categories.append("IP addresses")
    if _EMAIL_RE.search(text):
        categories.append("email addresses")
    if _SENSITIVE_RE.search(text):
        categories.append("sensitive terminology")
    return categories


def tlp_policy() -> list[dict[str, Any]]:
    """Return the TLP 2.0 policy table (the ground truth this gate applies)."""
    return [
        {"marking": f"TLP:{name}", **details}
        for name, details in sorted(TLP.items(), key=lambda item: -item[1]["rank"])
    ]


def check_tlp(text: str) -> dict[str, Any]:
    """Check a product's TLP marking against the FIRST TLP 2.0 rules.

    Flags a missing marking, conflicting markings, the deprecated ``TLP:WHITE``, and a
    permissive marking on content that looks sensitive.
    """
    tokens = [match.group(1).upper() for match in _TLP_RE.finditer(text or "")]
    normalised = ["CLEAR" if marking == "WHITE" else marking for marking in tokens]
    findings: list[dict[str, str]] = []

    if not tokens:
        findings.append(_finding("tlp-missing", MEDIUM, "Product carries no TLP marking"))
        effective = None
    else:
        unique = sorted(set(normalised))
        effective = unique[0] if len(unique) == 1 else None
        if len(unique) > 1:
            shown = ", ".join(f"TLP:{token}" for token in unique)
            findings.append(_finding("tlp-conflict", HIGH, f"Conflicting TLP markings: {shown}"))
        if "WHITE" in tokens:
            findings.append(_finding("tlp-deprecated", LOW, "TLP:WHITE is deprecated; use TLP:CLEAR"))
        permissive = sorted(token for token in unique if token in {"CLEAR", "GREEN"})
        sensitive = _sensitive_categories(text or "")
        if permissive and sensitive:
            shown = ", ".join(f"TLP:{token}" for token in permissive)
            findings.append(
                _finding(
                    "tlp-sensitive-permissive",
                    HIGH,
                    f"Permissive marking ({shown}) on content that looks sensitive ({', '.join(sensitive)})",
                )
            )

    return {
        "markings": [f"TLP:{token}" for token in tokens],
        "effective": f"TLP:{effective}" if effective else None,
        "findings": findings,
        "clean": not findings,
    }


def check_stix(bundle: Any) -> dict[str, Any]:
    """Check a STIX 2.1 bundle for structural conformance.

    Flags a non-bundle top level, a missing ``objects`` array, objects without a type or
    id, an id whose prefix does not match its type, duplicate ids, and a wrong or missing
    ``spec_version``.
    """
    findings: list[dict[str, str]] = []
    if not isinstance(bundle, dict):
        return {
            "valid": False,
            "findings": [_finding("stix-not-object", HIGH, "Top level is not a JSON object")],
            "by_severity": _severity_counts([_finding("stix-not-object", HIGH, "")]),
        }
    if bundle.get("type") != "bundle":
        findings.append(_finding("stix-not-bundle", HIGH, f"Top-level type is {bundle.get('type')!r}, not 'bundle'"))

    objects = bundle.get("objects")
    if not isinstance(objects, list):
        findings.append(_finding("stix-no-objects", HIGH, "Bundle has no 'objects' array"))
        return {"valid": False, "findings": findings, "by_severity": _severity_counts(findings)}

    seen: set[str] = set()
    for index, obj in enumerate(objects):
        pointer = f"objects[{index}]"
        if not isinstance(obj, dict):
            findings.append(_finding("stix-object-not-object", HIGH, f"{pointer} is not an object", pointer))
            continue
        object_type = obj.get("type")
        object_id = obj.get("id")
        if not object_type:
            findings.append(_finding("stix-missing-type", HIGH, f"{pointer} has no type", pointer))
        if not object_id:
            findings.append(_finding("stix-missing-id", HIGH, f"{pointer} has no id", pointer))
        else:
            if object_type and not object_id.startswith(f"{object_type}--"):
                findings.append(
                    _finding("stix-id-type-mismatch", HIGH, f"{pointer} id does not match its type", pointer)
                )
            if object_id in seen:
                findings.append(_finding("stix-duplicate-id", HIGH, f"{pointer} duplicates id {object_id}", pointer))
            seen.add(object_id)
        spec_version = obj.get("spec_version")
        if spec_version is not None and spec_version != "2.1":
            findings.append(
                _finding("stix-spec-version", MEDIUM, f"{pointer} spec_version is {spec_version!r}, not '2.1'", pointer)
            )
        elif spec_version is None:
            findings.append(_finding("stix-spec-version-missing", LOW, f"{pointer} has no spec_version", pointer))

    valid = not any(finding["severity"] == HIGH for finding in findings)
    return {"valid": valid, "findings": findings, "by_severity": _severity_counts(findings)}


def pre_share(document: Any) -> dict[str, Any]:
    """Run the full gate on a product (a STIX bundle, or any text/JSON).

    ``shareable`` is False only when a **high**-severity finding is present; lower
    findings are surfaced but do not block.
    """
    if isinstance(document, (dict, list)):
        data: Any = document
        text = json.dumps(document)
    else:
        text = str(document)
        try:
            data = json.loads(text)
        except ValueError:
            data = None

    tlp = check_tlp(text)
    stix = None
    if isinstance(data, dict) and ("objects" in data or data.get("type") == "bundle"):
        stix = check_stix(data)

    findings = list(tlp["findings"]) + (stix["findings"] if stix else [])
    return {
        "shareable": not any(finding["severity"] == HIGH for finding in findings),
        "effective_tlp": tlp["effective"],
        "tlp": tlp,
        "stix": stix,
        "findings": findings,
        "by_severity": _severity_counts(findings),
    }
