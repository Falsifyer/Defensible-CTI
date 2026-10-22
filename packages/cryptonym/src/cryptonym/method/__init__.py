"""cryptonym.method — the reusable core, re-exported from :mod:`cti_method`.

The core itself is owned by the ``cti-method`` package so the alias-specific tool is a
consumer, not the owner. This module keeps the historic import path working:

    from cryptonym.method import Assessment, Confidence, Judgement, filter_adjudication

The three rules the core encodes:

* a judgement carries **two independent axes** (confidence, probability), per claim;
* the evidence sets a **ceiling** on the declared confidence, and exceeding it is refused;
* a binary truth must be **earned from independent sources**, or it is contested.
"""

from __future__ import annotations

from cti_method.ach import (
    consistency_matrix,
    consistent_with_everything,
    discriminating_evidence,
    identity_supporting_evidence,
    inconsistency_counts,
    least_inconsistent,
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
from cti_method.confidence import Confidence, Judgement, Probability, parse_confidence, parse_probability
from cti_method.evidence import DIAGNOSTIC_TYPES, Consistency, Evidence, EvidenceType
from cti_method.grading import EvidenceProfile, ceiling, check_declared, derived_grade, profile
from cti_method.metrics import Confusion, calibration_table, confusion_from_calls

from cryptonym.assess.grading import assess_actor_pair
from cryptonym.evaluate.metrics import evaluate_adjudicated, evaluate_cases, evaluate_corpus
from cryptonym.model.assessment import Assessment, Hypothesis, Revision, load_assessment
from cryptonym.model.designation import Designation
from cryptonym.reconcile.graph import Linkage, Reconciliation
from cryptonym.snapshot import Snapshot

__all__ = [
    # grading (two axes, per claim, capped by the evidence)
    "Confidence",
    "Probability",
    "Judgement",
    "parse_confidence",
    "parse_probability",
    "EvidenceProfile",
    "profile",
    "ceiling",
    "derived_grade",
    "check_declared",
    # model
    "Designation",
    "Evidence",
    "EvidenceType",
    "Consistency",
    "DIAGNOSTIC_TYPES",
    "Hypothesis",
    "Assessment",
    "Revision",
    "load_assessment",
    # structured analysis
    "assess_actor_pair",
    "consistency_matrix",
    "inconsistency_counts",
    "least_inconsistent",
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
    # reconciliation
    "Linkage",
    "Reconciliation",
    # evaluation
    "Confusion",
    "confusion_from_calls",
    "calibration_table",
    "evaluate_cases",
    "evaluate_corpus",
    "evaluate_adjudicated",
    # provenance
    "Snapshot",
]
