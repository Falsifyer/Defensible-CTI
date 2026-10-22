"""Export designations and graded linkages as STIX 2.1.

Dependency-free: a STIX bundle is JSON, so Cryptonym builds the objects directly rather
than requiring ``stix2``. Designations become ``x-cryptonym-designation`` objects and each
linkage becomes an ``x-cryptonym-linkage`` object carrying the confidence and the
assessment id, so a consumer can always see *why* two names are linked — which a flat
``ThreatActor.aliases`` list never records.

If ``stix2`` is installed, the optional validation test parses the output with the real
library; the core does not depend on it.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from cti_method.stix import marking_object

from cryptonym.model.assessment import Assessment
from cryptonym.reconcile.graph import Reconciliation

#: Fixed namespace so identifiers are deterministic and reviewable across runs.
_NAMESPACE = uuid.UUID("1b7f3c4e-9a2d-4e6b-8c11-0d5e6f7a8b90")


def _id(prefix: str, value: str) -> str:
    return f"{prefix}--{uuid.uuid5(_NAMESPACE, value)}"


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def to_stix_objects(
    assessment: Assessment,
    reconciliation: Reconciliation | None = None,
    timestamp: str | None = None,
) -> list[dict[str, Any]]:
    """Return the STIX 2.1 objects for one assessment and its graded linkages."""
    stamp = timestamp or _now()
    marking = marking_object(assessment.tlp)
    objects: list[dict[str, Any]] = [marking]
    refs: dict[str, str] = {}

    for subject in assessment.subjects:
        object_id = _id("x-cryptonym-designation", subject.key)
        refs[subject.key] = object_id
        objects.append(
            {
                "type": "x-cryptonym-designation",
                "spec_version": "2.1",
                "id": object_id,
                "created": stamp,
                "modified": stamp,
                "vendor": subject.vendor,
                "name": subject.name,
                "source_url": subject.source_url,
                "tlp": subject.tlp,
                "object_marking_refs": [marking["id"]],
            }
        )

    for link in reconciliation.linkages if reconciliation else []:
        objects.append(
            {
                "type": "x-cryptonym-linkage",
                "spec_version": "2.1",
                "id": _id("x-cryptonym-linkage", f"{link.left}|{link.right}|{link.assessment_id}"),
                "created": stamp,
                "modified": stamp,
                "left": link.left,
                "right": link.right,
                "left_ref": refs.get(link.left),
                "right_ref": refs.get(link.right),
                "confidence": link.confidence.value,
                "assessment_id": link.assessment_id or assessment.id,
                "object_marking_refs": [marking["id"]],
            }
        )
    return objects


def to_stix_bundle(
    assessment: Assessment,
    reconciliation: Reconciliation | None = None,
    timestamp: str | None = None,
) -> dict[str, Any]:
    """Return a STIX 2.1 ``bundle`` wrapping the assessment objects."""
    objects = to_stix_objects(assessment, reconciliation, timestamp)
    return {"type": "bundle", "id": _id("bundle", assessment.id), "objects": objects}


def validate_export(bundle: dict[str, Any]) -> dict[str, Any]:
    """Validate the exported bundle with the suite's validator.

    The export is marked and structurally checked like any other bundle, so it can be
    gated by ``sharegate`` instead of travelling unmarked.
    """
    from cti_method.stix import validate_bundle

    return validate_bundle(bundle)
