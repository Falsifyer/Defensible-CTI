# The shared method core (`cti_method`)

Every tool in the family inherits one piece: **how a judgement is graded, what ceiling the
evidence sets on it, and how its truth is earned**. That piece is the `cti-method` package.
Import from it, never from a tool's internal modules.

```python
from cti_method import (
    Confidence, Probability, Judgement, Evidence, EvidenceType, Consistency,
    ceiling, derived_grade, check_declared,
    Truth, Standard, Source, SourceCategory, SourceKind, filter_adjudication,
    validate_bundle, marking_object, external_references,
)
```

`cryptonym.method` still exports the alias-specific surface (`Assessment`, `Hypothesis`,
`assess_actor_pair`, `Reconciliation`, `Snapshot`, the evaluation harness) for existing
consumers. It re-exports the core from `cti_method`; the core does not import the alias
package.

## The contract

| Group | Exports | Guarantees |
|---|---|---|
| Two-axis grading | `Confidence`, `Probability`, `Judgement`, `parse_*` | Confidence and probability are independent and per claim |
| **Grade ceiling** | `ceiling`, `derived_grade`, `check_declared` | A declared confidence above what the evidence supports is a high finding; no grade is `no-grade` |
| Model | `Designation`, `Evidence`, `EvidenceType`, `Consistency`, `Hypothesis`, `Assessment`, `Revision`, `load_assessment` | Nothing merges; a designation is a name, not an identity claim |
| Structured analysis | `assess_actor_pair`, `consistency_matrix`, `least_inconsistent`, `discriminating_evidence`, `identity_supporting_evidence`, `consistent_with_everything`, `inconsistency_counts` | ACH: the favoured hypothesis has the least inconsistent evidence |
| External truth | `Truth`, `Standard`, `Source`, `SourceCategory`, `SourceKind`, `Adjudication`, `Admissibility`, `filter_adjudication`, `independent_sources`, `parse_standard`, `validate_corpus` | A binary truth needs independent sources; disagreement is contested |
| Reconciliation | `Linkage`, `Reconciliation` | Clusters are computed at a threshold; the weakest link is exposed |
| Evaluation | `Confusion`, `confusion_from_calls`, `calibration_table`, `SPLITS`, `evaluate_*` | The false-merge rate, calibration and coverage are the headline |
| STIX | `validate_bundle`, `TLP`, `marking_object`, `effective_marking` | One validator, one severity table, official TLP 2.0 markings |
| Contract | `finding`, `severity_counts`, `exit_code`, `read_json`, `run`, `CannotCheck` | `0` clean, `1` refusal, `2` could not check |
| Traceability | `link`, `link_requirement`, `external_references` | A cited id is verified against the upstream file, never trusted as text |
| Provenance | `Snapshot` | A source's bytes and SHA-256 are recorded |

## Depending on it from another package

Inside the workspace, the dependency is declared as a workspace member:

```toml
dependencies = ["cti-method"]

[tool.uv.sources]
cti-method = { workspace = true }
```

Outside it, install the path first (`pip install -e packages/cti-method`). There is no
private repository to reach: the core is a package in this workspace with no runtime
dependencies.

Then keep the tool's own code about its *method* — not about confidence grading, the exit
codes or the STIX validator, which the core already owns.
