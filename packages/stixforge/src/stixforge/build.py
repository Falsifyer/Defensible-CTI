"""Turn a product document into a STIX 2.1 bundle.

The product is a JSON file: what the analyst wrote, the observables and the indicators,
the TLP, the creation timestamp, and the identifiers of the steps the product answers.
The bundle is **byte-reproducible**: identifiers are derived from content and ``created``
is required, so rebuilding the same product does not create a second version of the same
objects with a different timestamp under one id.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from cti_method.stix import marking_object
from cti_method.trace import external_references

# Namespace of this tool: identifiers are derived from it, never invented by hand.
NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "https://github.com/Falsifyer/Defensible-CTI")

SCO_TYPES = {
    "domain-name": "value",
    "ipv4-addr": "value",
    "ipv6-addr": "value",
    "url": "value",
    "file": "hashes",
    "email-addr": "value",
    "mac-addr": "value",
    "windows-registry-key": "key",
}


def _id(object_type: str, key: str) -> str:
    return f"{object_type}--{uuid.uuid5(NAMESPACE, f'{object_type}|{key}')}"


def _timestamp(value: str) -> str:
    """STIX 2.1 timestamps carry milliseconds; accept the shorter ISO form and normalise."""
    text = value.strip()
    if text.endswith("Z") and "." not in text:
        return text[:-1] + ".000Z"
    return text


def _sco(observable: dict[str, Any]) -> dict[str, Any]:
    """A STIX 2.1 cyber-observable: immutable, with no `created`, `modified` or marking.

    SCOs stopped carrying those properties in 2.1; the marking goes on the SDOs (the report
    and the indicators) that reference them. Emitting them made the bundle invalid for
    `stix2.parse`, which is how it was found.
    """
    object_type = observable.get("type")
    if object_type not in SCO_TYPES:
        raise ValueError(f"unsupported observable type: {object_type!r}")
    field = SCO_TYPES[object_type]
    value = observable.get(field)
    if not value:
        raise ValueError(f"observable {object_type} needs {field!r}")
    key = json.dumps(value, sort_keys=True) if isinstance(value, dict) else str(value)
    item = {"type": object_type, "spec_version": "2.1", "id": _id(object_type, key)}
    item[field] = value
    return item


def _confidence(value: Any) -> int | None:
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 100:
        raise ValueError("confidence must be an integer between 0 and 100")
    return value


def build(
    product: dict[str, Any],
    trace: dict[str, str | None] | None = None,
    trace_hashes: dict[str, str | None] | None = None,
) -> dict[str, Any]:
    """Build the bundle. Raises ValueError with the reason if the product is not usable.

    ``trace`` carries the verified identifiers of the upstream artifacts
    (``requirement_id``, ``assessment_id``, ``hunt_id``); they are emitted as
    ``external_references`` on the report so a consumer can walk back to the evidence.
    """
    title = (product.get("title") or "").strip()
    if not title:
        raise ValueError("the product needs a title")
    author_name = (product.get("author") or "").strip()
    if not author_name:
        raise ValueError("the product needs an author: the bundle must say who says this")

    stamp = (product.get("created") or "").strip()
    if not stamp:
        raise ValueError(
            "the product needs created (ISO 8601 UTC, ending in Z): without it the same "
            "identifiers would be stamped with a new timestamp on every build"
        )
    if not stamp.endswith("Z"):
        raise ValueError("created must be an ISO 8601 UTC timestamp (ending in Z)")
    stamp = _timestamp(stamp)

    raw_marking = product.get("tlp")
    if not isinstance(raw_marking, str) or not raw_marking.strip():
        raise ValueError(
            "the product needs tlp: a product with no marking must not default to TLP:CLEAR"
        )
    marking = marking_object(raw_marking)
    author_id = _id("identity", author_name)
    objects: list[dict[str, Any]] = [
        marking,
        {
            "type": "identity",
            "spec_version": "2.1",
            "id": author_id,
            "created": stamp,
            "modified": stamp,
            "name": author_name,
            "identity_class": product.get("author_class", "individual"),
            "object_marking_refs": [marking["id"]],
        },
    ]

    references: list[str] = []
    for observable in product.get("observables") or []:
        sco = _sco(observable)
        objects.append(sco)
        references.append(sco["id"])

    for indicator in product.get("indicators") or []:
        pattern = (indicator.get("pattern") or "").strip()
        if not pattern:
            raise ValueError("every indicator needs a STIX pattern")
        identifier = _id("indicator", f"{indicator.get('name', '')}|{pattern}")
        valid_until = indicator.get("valid_until") or product.get("valid_until")
        valid_from = _timestamp(str(indicator.get("valid_from") or stamp))
        if valid_until:
            valid_until = _timestamp(str(valid_until))
        if valid_until and str(valid_until) < str(valid_from):
            raise ValueError(f"indicator {indicator.get('name')!r}: valid_until is before valid_from")
        item = {
            "type": "indicator",
            "spec_version": "2.1",
            "id": identifier,
            "created": stamp,
            "modified": stamp,
            "created_by_ref": author_id,
            "object_marking_refs": [marking["id"]],
            "name": indicator.get("name") or pattern,
            "pattern": pattern,
            "pattern_type": indicator.get("pattern_type", "stix"),
            "valid_from": valid_from,
            "indicator_types": indicator.get("indicator_types", ["malicious-activity"]),
        }
        if valid_until:
            item["valid_until"] = valid_until
        confidence = _confidence(indicator.get("confidence"))
        if confidence is not None:
            item["confidence"] = confidence
        objects.append(item)
        references.append(identifier)

    for malware in product.get("malware") or []:
        name = (malware.get("name") or "").strip()
        if not name:
            raise ValueError("every malware object needs a name")
        identifier = _id("malware", name)
        objects.append({
            "type": "malware",
            "spec_version": "2.1",
            "id": identifier,
            "created": stamp,
            "modified": stamp,
            "created_by_ref": author_id,
            "object_marking_refs": [marking["id"]],
            "name": name,
            "is_family": bool(malware.get("is_family", False)),
            "malware_types": malware.get("malware_types", ["unknown"]),
        })
        references.append(identifier)

    if not references:
        raise ValueError("the product has nothing to share: add observables, indicators or malware")

    report_id = _id("report", product.get("id") or title)
    report = {
        "type": "report",
        "spec_version": "2.1",
        "id": report_id,
        "created": stamp,
        "modified": stamp,
        "created_by_ref": author_id,
        "object_marking_refs": [marking["id"]],
        "name": title,
        "published": _timestamp(str(product.get("published") or stamp)),
        "report_types": product.get("report_types", ["threat-report"]),
        "object_refs": references,
    }
    if product.get("summary"):
        report["description"] = product["summary"]
    external = external_references(trace or {}, trace_hashes)
    if external:
        report["external_references"] = external
    objects.append(report)

    return {
        "type": "bundle",
        "id": f"bundle--{uuid.uuid5(NAMESPACE, 'bundle|' + report_id)}",
        "objects": objects,
    }


def build_file(
    source: str | Path,
    output: str | Path | None = None,
    trace: dict[str, str | None] | None = None,
) -> dict[str, Any]:
    product = json.loads(Path(source).read_text(encoding="utf-8"))
    bundle = build(product, trace=trace)
    if output:
        Path(output).write_text(json.dumps(bundle, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return bundle
