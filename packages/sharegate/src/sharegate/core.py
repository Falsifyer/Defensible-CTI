"""The gate itself: TLP correctness and STIX 2.1 conformance.

Ground truth is external and citable: the FIRST **TLP 2.0** definitions and the **STIX
2.1** specification. Nothing here is a judgement call, which is the point — a compliance
gate earns trust by being objective.

The structural STIX check is **not** implemented here: it is
:func:`cti_method.stix.validate_bundle`, the same function the factory calls. The gate
adds what is its own: the TLP policy, read from the markings the objects actually
reference rather than from a regex over the serialised document.
"""

from __future__ import annotations

import json
import re
from typing import Any

from cti_method.contract import HIGH, LOW, MEDIUM, finding, has_high, severity_counts
from cti_method.stix import TLP, effective_marking, referenced_markings, validate_bundle

__all__ = ["check_stix", "check_tlp", "pre_share", "tlp_policy"]

_TLP_RE = re.compile(r"TLP\s*:\s*(RED|AMBER\+STRICT|AMBER|GREEN|CLEAR|WHITE)", re.IGNORECASE)
_IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_SENSITIVE_RE = re.compile(
    r"\b(victim|compromised|credentials?|passwords?|confidential|internal use|need[- ]to[- ]know|attribution)\b",
    re.IGNORECASE,
)


def tlp_policy() -> list[dict[str, Any]]:
    """Return the TLP 2.0 policy table (the ground truth this gate applies)."""
    table = [
        {"marking": entry["name"], "rank": entry["rank"], "summary": entry["summary"], "deprecated": False}
        for entry in TLP.values()
    ]
    table.append(
        {
            "marking": "TLP:WHITE",
            "rank": 1,
            "summary": "Deprecated (TLP 1.0). Use TLP:CLEAR.",
            "deprecated": True,
        }
    )
    return sorted(table, key=lambda item: -item["rank"])


def _sensitive_categories(text: str) -> list[str]:
    categories = []
    if _IPV4_RE.search(text):
        categories.append("IP addresses")
    if _EMAIL_RE.search(text):
        categories.append("email addresses")
    if _SENSITIVE_RE.search(text):
        categories.append("sensitive terminology")
    return categories


def _narrative_text(bundle: dict[str, Any]) -> str:
    """The text a human wrote, not the machine values of the observables.

    An IP address inside a cyber-observable is an indicator, not a confession: scoring it
    as "sensitive content" would block every TLP:CLEAR bundle of IOCs, which is the normal
    case in CTI. Only fields a human wrote are read.
    """
    parts: list[str] = []
    for obj in bundle.get("objects") or []:
        if not isinstance(obj, dict):
            continue
        if obj.get("type") == "marking-definition":
            continue
        for field_name in ("name", "description", "summary", "title"):
            value = obj.get(field_name)
            if isinstance(value, str):
                parts.append(value)
    return "\n".join(parts)


def check_tlp(document: str | dict[str, Any]) -> dict[str, Any]:
    """Check a product's TLP marking against the FIRST TLP 2.0 rules.

    For a STIX bundle the marking is resolved from ``object_marking_refs``: a marking
    that is defined but never referenced does not travel with the content. For plain text
    the labels are read from the text.

    Flags a missing marking, conflicting markings, the deprecated ``TLP:WHITE``, and a
    permissive marking on content that looks sensitive. The last one is a **medium**
    guard, not a blocker: it is a heuristic and it does not get to refuse a product.
    """
    findings: list[dict[str, str]] = []
    if isinstance(document, dict) and document.get("type") == "bundle":
        resolved, _ = referenced_markings(document)
        labels = sorted({item for values in resolved.values() for item in values})
        markings = [f"TLP:{item}" for item in labels]
        source = "references"
        narrative = _narrative_text(document)
        effective = effective_marking(document)
    else:
        text = document if isinstance(document, str) else json.dumps(document)
        labels = [match.group(1).upper() for match in _TLP_RE.finditer(text)]
        markings = [f"TLP:{item}" for item in labels]
        source = "text"
        narrative = text
        unique = sorted(set(labels))
        effective = unique[0] if len(unique) == 1 else None

    if not labels:
        findings.append(finding("tlp-missing", MEDIUM, "Product carries no TLP marking"))
    else:
        unique = sorted(set(labels))
        if len(unique) > 1:
            shown = ", ".join(f"TLP:{token}" for token in unique)
            findings.append(finding("tlp-conflict", HIGH, f"Conflicting TLP markings: {shown}"))
        if "WHITE" in labels:
            findings.append(finding("tlp-deprecated", LOW, "TLP:WHITE is TLP 1.0; use TLP:CLEAR"))
        permissive = [token for token in unique if token in {"CLEAR", "GREEN"}]
        sensitive = _sensitive_categories(narrative)
        if permissive and sensitive:
            shown = ", ".join(f"TLP:{token}" for token in permissive)
            findings.append(
                finding(
                    "tlp-sensitive-permissive",
                    MEDIUM,
                    f"Permissive marking ({shown}) on content that looks sensitive "
                    f"({', '.join(sensitive)}): review the marking",
                )
            )

    return {
        "markings": markings,
        "effective": f"TLP:{effective}" if effective else None,
        "source": source,
        "findings": findings,
        "clean": not findings,
    }


def check_stix(bundle: Any, today: str | None = None) -> dict[str, Any]:
    """Check a STIX 2.1 bundle with the suite's single validator."""
    result = validate_bundle(bundle, today=today)
    return {
        "valid": result["valid"],
        "checked": result.get("checked", True),
        "findings": result["findings"],
        "by_severity": result["by_severity"],
        "objects": result["objects"],
    }


def pre_share(
    document: Any, today: str | None = None, *, require_json: bool = False
) -> dict[str, Any]:
    """Run the full gate on a product (a STIX bundle, or any text/JSON).

    ``shareable`` is False only when a **high**-severity finding is present; lower
    findings are surfaced but do not block. With ``require_json`` an input that looks
    like JSON but does not parse is *not checked*: a corrupted bundle must not fall back
    to the text rule and leave as shareable.
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
            if require_json:
                failure = finding(
                    "input-unparseable",
                    HIGH,
                    "the input looks like JSON but could not be parsed: not checked",
                )
                return {
                    "shareable": False,
                    "checked": False,
                    "effective_tlp": None,
                    "tlp": None,
                    "stix": None,
                    "findings": [failure],
                    "by_severity": severity_counts([failure]),
                }

    tlp = check_tlp(data) if isinstance(data, dict) else check_tlp(text)
    stix = None
    if isinstance(data, dict) and ("objects" in data or data.get("type") == "bundle"):
        stix = check_stix(data, today=today)

    findings = list(tlp["findings"]) + (stix["findings"] if stix else [])
    return {
        "shareable": not has_high(findings),
        "checked": stix.get("checked", True) if stix else True,
        "effective_tlp": tlp["effective"],
        "tlp": tlp,
        "stix": stix,
        "findings": findings,
        "by_severity": severity_counts(findings),
    }
