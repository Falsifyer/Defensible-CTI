"""One STIX 2.1 validator, one severity table, and the official TLP 2.0 markings.

The suite had two validators — one in the factory, one in the gate — with different
severity tables, so the same bundle could be valid for one tool and invalid for the
other. This module is the single truth both call.

The TLP markings are the OASIS **TLP 2.0** marking definitions, taken from
``oasis-open/cti-stix-common-objects`` (``extension-definition-specifications/tlp-2.0``):
five labels, canonical identifiers and the property extension that carries the label.
``TLP:WHITE`` is recognised as the deprecated TLP 1.0 name for ``TLP:CLEAR`` and is
never emitted.
"""

from __future__ import annotations

import re
from typing import Any

from cti_method.contract import HIGH, LOW, MEDIUM, finding, has_high, severity_counts

SPEC_VERSION = "2.1"
#: Largest bundle the validator will walk. A bundle with a million objects is not checked,
#: it is refused: "not checked" is honest, "still running" is not.
MAX_OBJECTS = 20_000
TLP_EXTENSION_ID = "extension-definition--60a3c5c5-0d10-413e-aab3-9e08dde9e88d"

#: OASIS TLP 2.0 marking definitions. ``rank`` orders them from least to most restrictive.
TLP: dict[str, dict[str, Any]] = {
    "CLEAR": {
        "id": "marking-definition--94868c89-83c2-464b-929b-a1a8aa3c8487",
        "name": "TLP:CLEAR",
        "tlp_2_0": "clear",
        "rank": 1,
        "summary": "Recipients can spread this to the world; no limit on disclosure.",
    },
    "GREEN": {
        "id": "marking-definition--bab4a63c-aed9-4cf5-a766-dfca5abac2bb",
        "name": "TLP:GREEN",
        "tlp_2_0": "green",
        "rank": 2,
        "summary": "Recipients can spread this within their community, not publicly.",
    },
    "AMBER": {
        "id": "marking-definition--55d920b0-5e8b-4f79-9ee9-91f868d9b421",
        "name": "TLP:AMBER",
        "tlp_2_0": "amber",
        "rank": 3,
        "summary": "Limited disclosure within the organisation and its clients, need to know.",
    },
    "AMBER+STRICT": {
        "id": "marking-definition--939a9414-2ddd-4d32-a0cd-375ea402b003",
        "name": "TLP:AMBER+STRICT",
        "tlp_2_0": "amber+strict",
        "rank": 4,
        "summary": "Limited disclosure restricted to the recipient's own organisation.",
    },
    "RED": {
        "id": "marking-definition--e828b379-4e03-4974-9ac4-e53a884c97c1",
        "name": "TLP:RED",
        "tlp_2_0": "red",
        "rank": 5,
        "summary": "For the eyes and ears of individual recipients only; no further disclosure.",
    },
}

#: TLP 1.0 names and their TLP 2.0 replacements. ``WHITE`` is accepted and mapped, but
#: flagged as deprecated wherever it is read.
LEGACY: dict[str, str] = {"WHITE": "CLEAR"}

_TLP_RE = re.compile(r"TLP\s*:\s*(RED|AMBER\+STRICT|AMBER|GREEN|CLEAR|WHITE)", re.IGNORECASE)
_ID = re.compile(r"^(?P<type>[a-z0-9-]+)--[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")

#: Cyber-observables are immutable in 2.1: no ``created``, ``modified`` or marking.
SCO = {
    "artifact", "autonomous-system", "directory", "domain-name", "email-addr", "email-message",
    "file", "ipv4-addr", "ipv6-addr", "mac-addr", "mutex", "network-traffic", "process", "software",
    "url", "user-account", "windows-registry-key", "x509-certificate",
}
REQUIRED = ("type", "spec_version", "id", "created", "modified")
REQUIRED_SIN_MODIFIED = {"marking-definition"}
#: Objects that state how far something may travel. An unmarked one is not shareable.
MARKED = {"indicator", "malware", "report", "identity", "threat-actor", "campaign", "tool", "observed-data"}


def label(value: str) -> str:
    """Normalise ``amber``, ``TLP:amber`` or ``white`` to a TLP 2.0 key."""
    key = re.sub(r"^tlp\s*:\s*", "", (value or "").strip(), flags=re.IGNORECASE).upper()
    key = LEGACY.get(key, key)
    if key not in TLP:
        raise ValueError(f"unknown TLP marking {value!r}; expected one of: {', '.join(TLP)}")
    return key


def marking_object(value: str) -> dict[str, Any]:
    """The official TLP 2.0 marking-definition object for ``value``.

    A deprecated ``TLP:WHITE`` is refused rather than emitted: the factory does not build
    what the gate would flag as deprecated.
    """
    raw = re.sub(r"^tlp\s*:\s*", "", (value or "").strip(), flags=re.IGNORECASE).upper()
    if raw in LEGACY:
        raise ValueError(f"TLP:{raw} is deprecated (TLP 1.0); use TLP:{LEGACY[raw]}")
    key = label(value)
    entry = TLP[key]
    return {
        "type": "marking-definition",
        "spec_version": SPEC_VERSION,
        "id": entry["id"],
        "created": "2022-10-01T00:00:00.000Z",
        "name": entry["name"],
        "extensions": {
            TLP_EXTENSION_ID: {"extension_type": "property-extension", "tlp_2_0": entry["tlp_2_0"]}
        },
    }


def marking_label(obj: dict[str, Any]) -> str | None:
    """The TLP label a marking-definition object declares, or ``None`` if it is not TLP."""
    if obj.get("type") != "marking-definition":
        return None
    name = str(obj.get("name") or "")
    match = _TLP_RE.search(name)
    if match:
        return match.group(1).upper()
    extension = (obj.get("extensions") or {}).get(TLP_EXTENSION_ID) or {}
    value = extension.get("tlp_2_0")
    return str(value).upper() if value else None


def markings_in(bundle: dict[str, Any]) -> dict[str, str]:
    """``{marking-definition id: label}`` for the TLP markings the bundle defines."""
    found: dict[str, str] = {}
    for obj in bundle.get("objects") or []:
        if isinstance(obj, dict):
            declared = marking_label(obj)
            if declared and obj.get("id"):
                found[str(obj["id"])] = declared
    return found


def referenced_markings(bundle: dict[str, Any]) -> tuple[dict[str, set[str]], list[str]]:
    """Resolve ``object_marking_refs`` on every object.

    Returns ``{object id: {labels}}`` and the list of references that resolve to nothing.
    Resolution is by reference, not by scanning the serialised document: a marking that is
    defined but never referenced does not travel with the content, and must not be read as
    if it did.
    """
    defined = markings_in(bundle)
    resolved: dict[str, set[str]] = {}
    dangling: list[str] = []
    for obj in bundle.get("objects") or []:
        if not isinstance(obj, dict):
            continue
        for ref in obj.get("object_marking_refs") or []:
            if ref in defined:
                resolved.setdefault(str(obj.get("id")), set()).add(defined[ref])
            else:
                dangling.append(str(ref))
    return resolved, dangling


def effective_marking(bundle: dict[str, Any]) -> str | None:
    """The single marking every marked object shares, or ``None`` when they disagree."""
    resolved, _ = referenced_markings(bundle)
    labels = {item for values in resolved.values() for item in values}
    return labels.pop() if len(labels) == 1 else None


def _check_id(obj: dict[str, Any], pointer: str, findings: list[dict[str, str]]) -> None:
    ident = obj.get("id")
    object_type = obj.get("type")
    if not ident:
        findings.append(finding("stix-missing-id", HIGH, f"{pointer} has no id", pointer=pointer))
        return
    match = _ID.match(str(ident))
    if not match:
        findings.append(finding("stix-bad-id", HIGH, f"{pointer} id is not <type>--<uuid>", pointer=pointer))
    elif object_type and match.group("type") != object_type:
        findings.append(
            finding("stix-id-type-mismatch", HIGH, f"{pointer} id does not match its type", pointer=pointer)
        )


def validate_bundle(bundle: Any, today: str | None = None, max_objects: int = MAX_OBJECTS) -> dict[str, Any]:
    """Validate a STIX 2.1 bundle. One implementation, used by the factory and the gate.

    ``today`` (``YYYY-MM-DD``) enables the expiry check on indicators; without it the
    validator does not invent a clock.
    """
    findings: list[dict[str, str]] = []

    if not isinstance(bundle, dict):
        findings.append(finding("stix-not-object", HIGH, "Top level is not a JSON object"))
        return _result(findings, 0)
    if bundle.get("type") != "bundle":
        findings.append(finding("stix-not-bundle", HIGH, f"Top-level type is {bundle.get('type')!r}, not 'bundle'"))

    objects = bundle.get("objects")
    if not isinstance(objects, list) or not objects:
        findings.append(finding("stix-no-objects", HIGH, "Bundle has no non-empty 'objects' array"))
        return _result(findings, 0)
    if len(objects) > max_objects:
        findings.append(
            finding(
                "stix-too-large",
                HIGH,
                f"bundle has {len(objects):,} objects, over the {max_objects:,}-object limit: not checked",
            )
        )
        return _result(findings, len(objects), checked=False)

    bundle_id = str(bundle.get("id") or "")
    if not _ID.match(bundle_id) or not bundle_id.startswith("bundle--"):
        findings.append(finding("stix-bad-bundle-id", HIGH, "Bundle id is missing or not a bundle-- UUID"))

    seen: set[str] = set()
    by_id: dict[str, dict[str, Any]] = {}
    for index, obj in enumerate(objects):
        pointer = f"objects[{index}]"
        if not isinstance(obj, dict):
            findings.append(finding("stix-object-not-object", HIGH, f"{pointer} is not an object", pointer=pointer))
            continue
        object_type = obj.get("type")
        if not object_type:
            findings.append(finding("stix-missing-type", HIGH, f"{pointer} has no type", pointer=pointer))
            continue

        required: tuple[str, ...]
        if object_type in SCO:
            required = ("type", "spec_version", "id")
        elif object_type in REQUIRED_SIN_MODIFIED:
            required = ("type", "spec_version", "id", "created")
        else:
            required = REQUIRED
        missing = [name for name in required if not obj.get(name)]
        if missing:
            findings.append(
                finding("stix-missing-property", HIGH, f"{pointer} is missing: {', '.join(missing)}", pointer=pointer)
            )

        _check_id(obj, pointer, findings)
        ident = obj.get("id")
        if isinstance(ident, str):
            if ident in seen:
                findings.append(
                    finding("stix-duplicate-id", HIGH, f"{pointer} duplicates id {ident}", pointer=pointer)
                )
            seen.add(ident)
            by_id[ident] = obj

        spec_version = obj.get("spec_version")
        if spec_version is None:
            findings.append(
                finding("stix-spec-version-missing", HIGH, f"{pointer} has no spec_version", pointer=pointer)
            )
        elif spec_version != SPEC_VERSION:
            findings.append(
                finding(
                    "stix-spec-version",
                    HIGH,
                    f"{pointer} spec_version is {spec_version!r}, not '2.1'",
                    pointer=pointer,
                )
            )

        if object_type == "indicator":
            if not str(obj.get("pattern") or "").strip():
                findings.append(
                    finding("stix-indicator-no-pattern", HIGH, f"{pointer} has no pattern", pointer=pointer)
                )
            valid_from = obj.get("valid_from")
            valid_until = obj.get("valid_until")
            if not valid_from:
                findings.append(
                    finding("stix-indicator-no-valid-from", HIGH, f"{pointer} has no valid_from", pointer=pointer)
                )
            if valid_from and valid_until and str(valid_until) < str(valid_from):
                findings.append(
                    finding("stix-bad-validity", HIGH, f"{pointer} valid_until is before valid_from", pointer=pointer)
                )
            if today and valid_until and str(valid_until)[:10] < today:
                findings.append(
                    finding("stix-expired-indicator", MEDIUM, f"{pointer} expired on {valid_until}", pointer=pointer)
                )
        if object_type == "report" and not obj.get("object_refs"):
            findings.append(
                finding("stix-report-no-refs", HIGH, f"{pointer} report references nothing", pointer=pointer)
            )

    # References must resolve inside the bundle.
    for ident, obj in by_id.items():
        where = f"{obj.get('type')} {ident}"[:80]
        for field_name in ("object_refs", "object_marking_refs"):
            for ref in obj.get(field_name) or []:
                if ref not in by_id:
                    findings.append(
                        finding(
                            "stix-unresolved-reference",
                            HIGH,
                            f"{where}: {field_name} -> {ref} is not in the bundle",
                            where=where,
                        )
                    )
        creator = obj.get("created_by_ref")
        if creator and creator not in by_id:
            findings.append(
                finding(
                    "stix-unresolved-reference",
                    HIGH,
                    f"{where}: created_by_ref -> {creator} is not in the bundle",
                    where=where,
                )
            )

    if today:
        indicators = [obj for obj in by_id.values() if obj.get("type") == "indicator"]
        expired = [
            obj
            for obj in indicators
            if obj.get("valid_until") and str(obj["valid_until"])[:10] < today
        ]
        if indicators and len(expired) == len(indicators):
            findings.append(
                finding(
                    "stix-all-indicators-expired",
                    HIGH,
                    f"every indicator in the bundle expired before {today}: "
                    "the product is not shareable as intelligence",
                )
            )

    # Marking: defined, referenced, and not deprecated.
    definitions = markings_in(bundle)
    if not definitions:
        findings.append(
            finding("stix-no-marking-definition", MEDIUM, "The bundle defines no TLP marking", pointer="objects")
        )
    for ident, obj in by_id.items():
        object_type = obj.get("type")
        if object_type not in MARKED:
            continue
        refs = obj.get("object_marking_refs") or []
        where = f"{object_type} {ident}"[:80]
        if not refs:
            findings.append(
                finding(
                    "stix-no-marking",
                    HIGH,
                    f"{where}: no TLP marking, so the bundle does not say how far it may travel",
                    where=where,
                )
            )
            continue
        for ref in refs:
            declared = definitions.get(ref)
            if declared is None:
                continue  # unresolved references are already reported
            if declared == "WHITE":
                findings.append(
                    finding("tlp-deprecated", LOW, f"{where}: TLP:WHITE is TLP 1.0; use TLP:CLEAR", where=where)
                )
            elif declared not in TLP:
                findings.append(
                    finding("tlp-unknown", MEDIUM, f"{where}: marking {ref} is not a TLP 2.0 label", where=where)
                )

    return _result(findings, len(objects))


def _result(findings: list[dict[str, str]], objects: int, checked: bool = True) -> dict[str, Any]:
    counts = severity_counts(findings)
    return {
        "valid": not has_high(findings),
        "checked": checked,
        "findings": findings,
        "objects": objects,
        "by_severity": counts,
        "high": counts[HIGH],
        "medium": counts[MEDIUM],
    }
