"""Export an assessment to MISP Galaxy form, marked as *assessed*, not asserted.

The distinction matters: an asserted alias says "these are the same". An assessed alias
says "a vendor reported an overlap, which we graded at moderate confidence". MISP
consumers must be able to tell the two apart, so the flag and the per-value confidence
travel with the cluster.
"""

from __future__ import annotations

from typing import Any

from cryptonym.model.assessment import Assessment
from cryptonym.reconcile.graph import Reconciliation


def to_misp_galaxy_cluster(
    assessment: Assessment, reconciliation: Reconciliation | None = None
) -> dict[str, Any]:
    """Return a Galaxy-cluster shaped dict describing the assessment."""
    meta: dict[str, Any] = {
        "cryptonym:assessment_id": assessment.id,
        "cryptonym:version": assessment.version,
        "cryptonym:confidence": assessment.judgement.confidence.value,
        "cryptonym:tlp": assessment.tlp,
    }
    if assessment.judgement.probability is not None:
        meta["cryptonym:probability"] = assessment.judgement.probability.value

    values = [
        {
            "value": f"{subject.vendor}:{subject.name}",
            "description": f"{subject.name} ({subject.vendor})",
            "meta": {
                "vendor": subject.vendor,
                "name": subject.name,
                "source_url": subject.source_url,
                "cryptonym:confidence": assessment.judgement.confidence.value,
            },
        }
        for subject in assessment.subjects
    ]

    if reconciliation is not None:
        meta["cryptonym:linkages"] = [
            {"left": link.left, "right": link.right, "confidence": link.confidence.value}
            for link in reconciliation.linkages
        ]

    return {
        "description": assessment.question,
        "meta": meta,
        "values": values,
        "aliases_assessed_not_asserted": True,
    }
