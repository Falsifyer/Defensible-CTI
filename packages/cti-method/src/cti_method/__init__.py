"""cti-method — the shared core of the suite.

The one place the six tools inherit their rules from:

* how a claim is graded, and **what ceiling the evidence sets on that grade**;
* how evidence is typed by diagnostic strength;
* how competing hypotheses are compared (ACH, least-inconsistent);
* how an external truth is adjudicated and filtered;
* one STIX 2.1 validator with one severity table, and the official TLP 2.0 markings;
* one exit-code contract (``0`` clean, ``1`` refusal, ``2`` could not check);
* how artifacts trace to one another across the cycle.

Import from here, not from the submodules: this surface is the stable contract.
"""

from __future__ import annotations

__version__ = "0.2.0"

from cti_method.ach import (
    addressed_hypotheses,
    consistency_matrix,
    consistent_with_everything,
    discriminating_evidence,
    identity_supporting_evidence,
    inconsistency_counts,
    inconsistency_scores,
    least_inconsistent,
    ranking_basis,
    supported_hypotheses,
    tied_at_top,
)
from cti_method.adjudication import (
    Adjudication,
    Admissibility,
    Source,
    SourceCategory,
    SourceKind,
    Standard,
    Truth,
    filter_adjudication,
    independent_sources,
    parse_standard,
    validate_corpus,
)
from cti_method.confidence import (
    Confidence,
    Judgement,
    Probability,
    parse_confidence,
    parse_probability,
)
from cti_method.contract import (
    CANNOT_CHECK,
    FINDING,
    HIGH,
    LOW,
    MEDIUM,
    OK,
    CannotCheck,
    exit_code,
    finding,
    has_high,
    read_json,
    read_text,
    severity_counts,
)
from cti_method.evidence import DIAGNOSTIC_TYPES, Consistency, Evidence, EvidenceType
from cti_method.grading import EvidenceProfile, ceiling, check_declared, derived_grade, policy, profile
from cti_method.metrics import (
    PROBABILITY_POINTS,
    SPLITS,
    Confusion,
    calibration_table,
    confusion_from_calls,
    probability_calibration,
)
from cti_method.sources import SourceRef, independent_ids, registry
from cti_method.stix import (
    TLP,
    TLP_EXTENSION_ID,
    effective_marking,
    label,
    marking_label,
    marking_object,
    markings_in,
    referenced_markings,
    validate_bundle,
)
from cti_method.trace import (
    LINK_FIELDS,
    content_hash,
    external_references,
    hash_field,
    id_of,
    link,
    link_requirement,
    requirement_ids,
)

__all__ = [
    "__version__",
    # contract
    "OK",
    "FINDING",
    "CANNOT_CHECK",
    "HIGH",
    "MEDIUM",
    "LOW",
    "CannotCheck",
    "finding",
    "severity_counts",
    "has_high",
    "exit_code",
    "read_text",
    "read_json",
    # grading
    "Confidence",
    "Probability",
    "Judgement",
    "parse_confidence",
    "parse_probability",
    "Evidence",
    "EvidenceType",
    "Consistency",
    "DIAGNOSTIC_TYPES",
    "EvidenceProfile",
    "profile",
    "ceiling",
    "derived_grade",
    "check_declared",
    "policy",
    # ACH
    "consistency_matrix",
    "addressed_hypotheses",
    "inconsistency_counts",
    "inconsistency_scores",
    "least_inconsistent",
    "ranking_basis",
    "supported_hypotheses",
    "tied_at_top",
    "discriminating_evidence",
    "identity_supporting_evidence",
    "consistent_with_everything",
    # external truth
    "Truth",
    "Standard",
    "Source",
    "SourceCategory",
    "SourceKind",
    "Adjudication",
    "Admissibility",
    "filter_adjudication",
    "independent_sources",
    "parse_standard",
    "validate_corpus",
    # metrics
    "SPLITS",
    "Confusion",
    "confusion_from_calls",
    "calibration_table",
    "PROBABILITY_POINTS",
    "probability_calibration",
    # STIX
    "TLP",
    "TLP_EXTENSION_ID",
    "label",
    "marking_object",
    "marking_label",
    "markings_in",
    "referenced_markings",
    "effective_marking",
    "validate_bundle",
    # sources and traceability
    "SourceRef",
    "registry",
    "independent_ids",
    "LINK_FIELDS",
    "id_of",
    "content_hash",
    "hash_field",
    "link",
    "link_requirement",
    "requirement_ids",
    "external_references",
]
