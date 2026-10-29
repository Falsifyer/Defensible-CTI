# Method

## What this tool is

A general **graded-assessment ledger**, built on the shared core `cti_method`. Where
Cryptonym specialises in actor aliases, assessment-mcp grades **any** claim: a compromise,
a campaign attribution, a vulnerability's exploitation status — anything with competing
explanations.

## The shared core it inherits

| Concern | Owner |
|---|---|
| Two-axis grading (confidence, probability) | `cti_method` |
| Evidence typed by diagnostic strength | `cti_method` |
| **The ceiling the evidence sets on the grade** | `cti_method.grading` |
| ACH over arbitrary hypotheses | `cti_method` |
| External-truth filter (independence, admissibility) | `cti_method` |
| Evaluation (false-merge rate, calibration) | `cti_method` |
| The general workflow and the ledger | this tool |

The tool imports `cti_method` directly. It does **not** import the alias package: the
generic tool is not a consumer of the specific one.

## The claim

A claim is a **question**, a body of **evidence**, competing **hypotheses** and a **grade**:

```json
{
  "schema_version": "1.0",
  "id": "claim-001",
  "question": "Did actor X compromise host Y?",
  "hypotheses": ["compromise", "benign"],
  "evidence": [
    {"id": "E1", "statement": "unique implant on host Y", "source": "telemetry A",
     "type": "code", "consistency": {"compromise": "C", "benign": "I"}},
    {"id": "E2", "statement": "the C2 certificate matches a known cluster", "source": "telemetry B",
     "type": "infrastructure", "consistency": {"compromise": "C", "benign": "I"}}
  ],
  "judgement": {
    "confidence": "high",
    "probability": "very_likely",
    "probability_of": "compromise"
  }
}
```

- The **favoured hypothesis** is the one with the least inconsistent evidence, not the
  loudest. Hypotheses may be any labels, but there must be **at least two**.
- The ranking counts **independent voices**, not items: restating one source does not move
  it. When the best score is shared, `tied` names the hypotheses and `favoured` is `null`;
  the ceiling is the most restrictive across them.
- **Confidence** and **probability** are separate; a claim can be *very likely* at *low*
  confidence or *roughly even* at *high* confidence.
- Add an **`adjudication`** and the external-truth filter decides whether the declared
  truth is admissible (independent sources, no unearned merge).

## The grade is not declared and printed: it is capped

A declared confidence is a claim about the evidence, so the evidence sets a ceiling:

| Ceiling | Requires |
|---|---|
| `low` | nothing diagnostic discriminates — shared tradecraft, vendor wording, structural overlap |
| `moderate` | at least one diagnostic item discriminates, all from one source |
| `high` | at least one diagnostic item discriminates **and** two independent sources contribute diagnostics |

A grade **below** the ceiling is allowed: an analyst may be more cautious than the evidence.
A grade **above** it is `grade-exceeds-evidence`, a high finding, and the run exits 1. A
claim that declares no grade is `no-grade`, also high: there is no silent default.

Independence is by source string, normalised. That is a coarse proxy — a dossier that needs
finer independence should model its sources as sources — but it is checkable and it fails
closed.

## Two modes, one independence rule

The table above grades an ACH. Not every claim is a dispute between alternatives: "MITRE
records C0029 as a campaign" has no competing hypothesis, and grading it by what
distinguishes actors caps it at `low` for the wrong reason. The same function therefore has
two modes:

| Mode | Hypotheses | What counts | Ceiling |
|---|---|---|---|
| `ach` | two or more | diagnostic items that discriminate | `low` / `moderate` / `high` as above |
| `claim` | one — the claim itself | items that bear **directly** on the claim (`direct`), whatever their evidence type | no direct item `low`; one independent source `moderate`; two `high` |

In both modes independence is structural and contradiction lowers the ceiling — in `claim`
mode there is no alternative to weigh, so only the first applies. A claim with **no**
hypothesis is refused (`no-claim`). The policy is exported by
`cti_method.grading.policy()` so a consumer renders it instead of restating it.

## The chain

`assessment assess` can be run three ways that matter:

- `--against previous-judgement.json` re-derives the previous step's ranking and ceiling and
  reports `judgement-mismatch` if the dossier changed after that judgement was produced;
- `--register pir.json` verifies that `requirement_id` exists in the register;
- `--append ledger.jsonl` writes the verdict to the ledger, but only when the verdict is not
  refused.

## The ledger

Each line is an entry with `seq`, `created_at`, `tool`, `claim_id`, `claim_hash`, the
`claim` itself, `prev_hash` and `hash`. The hash covers the entry without itself, and
`prev_hash` chains to the line before. `ledger --verify` walks the chain and reports the
first line where it breaks: editing a claim, dropping a line in the middle or reordering two
lines is detected.

A **tail truncation** leaves a valid prefix, so the chain alone cannot see it. `--head-out`
writes a manifest with the head and length, and `ledger --verify --head-file` (or
`--expect-head`/`--expect-count`) fails when the file is shorter or ends somewhere else. It
is tamper-evident, not tamper-proof: whoever can rewrite the whole file can recompute the
chain. To prove *when*, publish the head hash somewhere you do not control.

## What it does not do

- It does not source or verify evidence; that is the analyst's work.
- It does not decide; it grades and states what would change the grade.
- "Admissible" means the truth was earned from independent sources, not that it is correct.
