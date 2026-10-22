# Reproducible evaluation

The harness that scores Cryptonym's **method** — not just its code.

```bash
# Reproduce the single published judgement from the published evidence:
python evaluation/run_evaluation.py --dossier assessments/voltzite-vs-volt-typhoon/assessment.json

# Score the golden-pair corpus; fail if the summary drifted from the baseline:
python evaluation/run_evaluation.py --corpus --check
```

## What it reports

- a **confusion matrix** over the corpus (positive class: "same actor"), reported **per
  split** — `development` and `held-out` — and overall;
- the **false-merge rate** (the costly error) and the **false-split rate**, separately;
- a **calibration table** — accuracy per confidence level, per split.

Held-out results are never averaged into the development ones: a method graded on the
cases it was tuned against proves nothing.

## Structure

- `golden_pairs/pairs.json` — adjudicated cases: evidence + truth.
- `golden_pairs/expected.json` — the committed summary `--check` compares against.
- `../src/cryptonym/evaluate/metrics.py` — the metrics (unit-tested).
- `run_evaluation.py` — the runner used by CI.

## Interpretation

See [../docs/evaluating-alias-reconciliation.md](../docs/evaluating-alias-reconciliation.md).
The corpus is **illustrative**: it proves the engine re-derives a graded judgement and
that the harness reports errors, not that the method is right about the world. Real
accuracy needs independent, held-out adjudications that a single-author project does not
own.
