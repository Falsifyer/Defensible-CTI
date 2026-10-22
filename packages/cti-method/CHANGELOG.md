# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## 0.1.0 — 2026-10-22

- First version. The shared core extracted from `cryptonym`: two-axis grading, the
  evidence-derived **ceiling** (`high` needs a diagnostic discriminating item and two
  independent sources), ACH over arbitrary hypotheses, the adjudication filter, the
  confusion/calibration arithmetic, **one** STIX 2.1 validator, the official TLP 2.0
  markings, the `0/1/2` contract and the artifact trace.

- **Source registry** (`sources.py`): independence is structural (`source_id`,
  `publisher`, `derived_from`), not a string comparison. Two reports from one publisher are
  one voice; a derived source is not a second voice.
- **Weighted ACH**: items carry an Admiralty band and the ranking uses weighted
  inconsistency (`inconsistency_scores`); without a band every item weighs the same.
- **The ceiling considers contradiction**: if diagnostic evidence against the favoured
  hypothesis outweighs the evidence for it, the ceiling drops a step.
- **Probability calibration** (Brier + per-band reliability) alongside confidence
  calibration.
- **The trace pins content**: `content_hash`, `<kind>_hash` verification and
  `<id>@<sha256:12>` in `external_references`; `id_of` is explicit per artifact kind.
- **Limits**: 8 MiB and 64 levels on input, 20,000 objects on a bundle (`checked: false`,
  exit 2). The schemas now ship with the package, and `--strict` can validate a judgement.

