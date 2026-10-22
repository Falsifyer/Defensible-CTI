# The shared method core (`cryptonym.method`)

Every Cryptonym-family tool inherits one piece: **how a judgement is graded and how its
truth is earned**. That piece is `cryptonym.method`. Import from it, never from the
internal modules.

```python
from cryptonym.method import (
    Assessment, Confidence, Judgement, Evidence, EvidenceType, Consistency,
    Truth, Standard, Source, SourceCategory, SourceKind, filter_adjudication,
    assess_actor_pair,
)
```

## The contract

| Group | Exports | Guarantees |
|---|---|---|
| Two-axis grading | `Confidence`, `Probability`, `Judgement`, `parse_*` | Confidence and probability are independent and per claim |
| Model | `Designation`, `Evidence`, `EvidenceType`, `Consistency`, `Hypothesis`, `Assessment`, `Revision`, `load_assessment` | Nothing merges; a designation is a name, not an identity claim |
| Structured analysis | `assess_actor_pair`, `consistency_matrix`, `least_inconsistent`, `discriminating_evidence`, `identity_supporting_evidence`, `consistent_with_everything`, `inconsistency_counts` | ACH: the favoured hypothesis has the least inconsistent evidence |
| External truth | `Truth`, `Standard`, `Source`, `SourceCategory`, `SourceKind`, `Adjudication`, `Admissibility`, `filter_adjudication`, `independent_sources`, `parse_standard`, `validate_corpus` | A binary truth needs independent sources; disagreement is contested |
| Reconciliation | `Linkage`, `Reconciliation` | Clusters are computed at a threshold; the weakest link is exposed |
| Evaluation | `Confusion`, `confusion_from_calls`, `calibration_table`, `evaluate_cases`, `evaluate_corpus`, `evaluate_adjudicated` | The false-merge rate, calibration and coverage are the headline |
| Provenance | `Snapshot` | A source's bytes and SHA-256 are recorded |

## Depending on it from another repository

Each family tool installs the core (editable for local work, or from the private repo):

```bash
pip install -e "/root/cryptonym"        # local, editable
# or, from the private GitHub repository (token in the URL or a credential helper):
pip install "cryptonym @ git+https://github.com/ME0094/cryptonym.git"
```

Then use the method surface directly, and keep the tool's own code about its *method* —
not about confidence grading, which the core already owns.
