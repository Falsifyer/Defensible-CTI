# Adjudicated corpus

Cases whose truth is an **external adjudication**, not the author's assertion, filtered
for admissibility. The standard is [../../docs/adjudication.md](../../docs/adjudication.md).

```bash
python evaluation/run_evaluation.py --adjudicated --check --strict
cryptonym adjudicate evaluation/adjudicated/corpus.json --strict
```

## Files

- `corpus.json` — the cases. Each carries the analyst's `evidence` (the engine's input)
  and an `adjudication` (the external truth, its standard and its sources).
- `expected.json` — the committed baseline `--check` compares against: metrics,
  calibration, **coverage** and standards.
- `schema.json` — the JSON Schema for the corpus.

## What this corpus is seed material

It is deliberately small. The point of the filter is to make the weak cases **visible**:
this seed contains 2 admissible binary cases, 2 `contested`, and 0 `unadjudicated`; both
admissible cases are scored, one contested case ties, and two cases have no diagnostic
support. The coverage/calls/abstentions table is printed with the metrics precisely so that
"false-merge rate 0.0 over 2 cases" reads as what it is.

The value is not the number. It is that the number cannot be inflated: a new case only
enters the error rates if independent sources assert its truth, disagreement is recorded
as `contested`, and `--strict` fails on an ungrounded binary claim.
