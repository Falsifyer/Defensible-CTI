"""Serve assessments over TAXII 2.1.

Cryptonym's method objects (graded linkages) are only useful if they travel. A TAXII
collection lets a partner pull the judgement *and its provenance* rather than a
flattened indicator. This is the envelope assembly; wiring it to a live collection is
deployment, not method.
"""

from __future__ import annotations

from typing import Any

from cryptonym.export.stix_bundle import to_stix_objects
from cryptonym.model.assessment import Assessment
from cryptonym.reconcile.graph import Reconciliation


def to_taxii_envelope(
    assessment: Assessment,
    reconciliation: Reconciliation | None = None,
    timestamp: str | None = None,
) -> dict[str, Any]:
    """Return a TAXII 2.1 ``envelope`` (``objects`` + ``more``) for an assessment."""
    return {
        "more": False,
        "objects": to_stix_objects(assessment, reconciliation, timestamp),
    }
