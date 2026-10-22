"""cryptonym.method — the shared, reusable assessment core.

This is the one piece every tool in the Cryptonym family inherits: how a claim is graded,
how evidence is typed by diagnostic strength, how competing hypotheses are compared, how
an external truth is adjudicated and filtered, how graded linkages reconcile, and how a
source is snapshotted.

Import from **here**, not from the internal modules. This surface is the stable contract;
everything under ``cryptonym.model``, ``cryptonym.assess``, ``cryptonym.evaluate``,
``cryptonym.reconcile`` and ``cryptonym.snapshot`` is an implementation detail that may
move.

    from cryptonym.method import Assessment, Confidence, Judgement, filter_adjudication

The three rules the core encodes:

* a judgement carries **two independent axes** (confidence, probability), per claim;
* a binary truth must be **earned from independent sources**, or it is contested;
* nothing is merged without **provenance** — a merge is a hypothesis, not a fact.
"""

from __future__ import annotations

from cryptonym.assess.ach import (
    consistency_matrix,
    consistent_with_everything,
    discriminating_evidence,
    identity_supporting_evidence,
    inconsistency_counts,
    least_inconsistent,
)
from cryptonym.assess.grading import assess_actor_pair
from cryptonym.evaluate.adjudication import (
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
from cryptonym.evaluate.metrics import (
    Confusion,
    calibration_table,
    confusion_from_calls,
    evaluate_adjudicated,
    evaluate_cases,
    evaluate_corpus,
)
from cryptonym.model.assessment import Assessment, Hypothesis, Revision, load_assessment
from cryptonym.model.confidence import (
    Confidence,
    Judgement,
    Probability,
    parse_confidence,
    parse_probability,
)
from cryptonym.model.designation import Designation
from cryptonym.model.evidence import DIAGNOSTIC_TYPES, Consistency, Evidence, EvidenceType
from cryptonym.reconcile.graph import Linkage, Reconciliation
from cryptonym.snapshot import Snapshot

__all__ = [
    # grading (two axes, per claim)
    "Confidence",
    "Probability",
    "Judgement",
    "parse_confidence",
    "parse_probability",
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
