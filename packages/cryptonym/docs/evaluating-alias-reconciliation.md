# Evaluating alias reconciliation without fooling yourself

**Status: harness implemented (v0.2.0), reported per split.** Development and held-out
results are never averaged: the held-out result is the one that counts. What remains is
independent adjudications, not mechanics.

A tool that reports "assessment produced" tells you about the tool, not about the
judgement. For a claim about a *method*, the evaluation must test the method, and be
honest about what it cannot test.

## What must be measured

1. **False merges.** The expensive error. Two designations wrongly treated as one actor
   contaminates every downstream decision. This, not recall, is the headline number.
2. **False splits.** The cheap error: two designations kept apart that are the same.
3. **Calibration.** Are the `moderate`-confidence merges actually more reliable than the
   `low`-confidence ones? A grading scheme that does not calibrate is decoration.

## How it is implemented

- **Confusion and rates** — `cryptonym.evaluate.metrics` (`false_merge_rate`,
  `false_split_rate`), reported separately because they trade off.
- **Calibration** — accuracy per confidence level (`calibration_table`).
- **Golden-pair corpus** — `evaluation/golden_pairs/pairs.json`: each case is a body of
  evidence, an adjudicated truth and a **split** (`development` or `held-out`). The engine
  must re-derive the favourite hypothesis; the harness asks whether it agrees and at what
  confidence, and reports every split separately.
- **Adjudicated corpus** — `evaluation/adjudicated/corpus.json`: truth is an external
  adjudication, filtered for **independence** and **admissibility**
  ([adjudication.md](adjudication.md)). Only admissible binary truths enter the error
  rates; `contested` and `unadjudicated` cases are reported as **coverage**, and
  `--strict` rejects an unearned binary claim.
- **Reproducibility** — a fixed summary is committed
  (`evaluation/golden_pairs/expected.json`) and CI runs
  `run_evaluation.py --corpus --check`, failing on drift.
- **Source snapshots** — `cryptonym.snapshot` records a source's bytes and SHA-256, so the
  evidence in an assessment can be tied to the exact document it came from.

## What this cannot prove

- **The corpus is illustrative.** It measures the *engine and the harness*, not
  real-world attribution accuracy. The evidence in each case is authored, so agreement
  with the truth shows the method is self-consistent, not that it is right about the
  world.
- **Ground truth for attribution is scarce and often classified.** Any golden set is
  small, partial and lagging.
- **Vendors do not publish their linkage logic**, so evidence is often linguistic and
  structural — the weakest kind — and the harness says so.
- **Confidence levels on an illustrative corpus calibrate trivially.** Real calibration
  needs a larger, independently adjudicated set with genuine disagreements; the
  calibration *mechanism* is tested directly in `tests/test_evaluate.py`.

The defensible claim is narrow: *given a body of evidence and a declared standard,
Cryptonym re-derives a graded, falsifiable judgement, reproducibly, exposes what would break
the tie, and reports its own false-merge rate.* The claim it does **not** make is that it
will tell you who an actor is.
