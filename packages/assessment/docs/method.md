# Method

## What this tool is

A general **graded-assessment ledger**, built on the shared core `cryptonym.method`. Where
Cryptonym specialises in actor aliases, assessment-mcp grades **any** claim: a compromise,
a campaign attribution, a vulnerability's exploitation status — anything with competing
explanations.

## The shared core it inherits

| Concern | Owner |
|---|---|
| Two-axis grading (confidence, probability) | `cryptonym.method` |
| Evidence typed by diagnostic strength | `cryptonym.method` |
| ACH over arbitrary hypotheses | `cryptonym.method` |
| External-truth filter (independence, admissibility) | `cryptonym.method` |
| Evaluation (false-merge rate, calibration) | `cryptonym.method` |
| The general workflow and the ledger | this tool |

The core is imported lazily: the offline parts of this tool work without it, but the
graded paths fail loudly if it is missing.

## The claim

A claim is a **question**, a body of **evidence**, competing **hypotheses** and a **grade**:

```json
{
  "question": "Did actor X compromise host Y?",
  "hypotheses": ["compromise", "benign"],
  "evidence": [
    {"id": "E1", "statement": "unique implant on host Y", "source": "telemetry",
     "type": "code", "consistency": {"compromise": "C", "benign": "I"}}
  ],
  "judgement": {"confidence": "high", "probability": "very_likely"}
}
```

- The **favoured hypothesis** is the one with the least inconsistent evidence, not the
  loudest. Hypotheses may be any labels.
- **Confidence** and **probability** are separate; a claim can be *very likely* at *low*
  confidence or *roughly even* at *high* confidence.
- Add an **`adjudication`** and the external-truth filter decides whether the declared
  truth is admissible (independent sources, no unearned merge).

## The ledger

`append_claim_to_ledger` writes each graded claim as one JSON line, so a body of
judgements accumulates, is diffable, and can be re-read. The ledger is plain text you own.

## What it does not do

- It does not source or verify evidence; that is the analyst's work.
- It does not decide; it grades and states what would change the grade.
- "Admissible" means the truth was earned from independent sources, not that it is correct.
