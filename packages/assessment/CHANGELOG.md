# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## Unreleased

### Fixed

- **`--strict` accepts the verdict the tool emits**: the verdict now carries
  `grade_findings`, which the published schema requires.
- **A malformed claim is exit 2**, not a traceback with exit 1.
- **Ties are reported** as `tied` and `favoured: null`; the ceiling is the most restrictive
  across the tied hypotheses.
- **The ledger can be anchored.** `--head-out` writes the head and length; `ledger --verify
  --head-file` (or `--expect-head`/`--expect-count`) detects a truncated tail, which the
  bare chain cannot see.

## 0.3.0 — 2026-10-28

### Changed

- **A claim may have one hypothesis.** `assess` now grades a factual claim (one hypothesis,
  mode `claim`) instead of refusing it; `weigh` still requires two, because ranking a
  single option is not analysis. A claim with **no** hypothesis is refused (`no-claim`).
- `assess` reports the `mode` it applied, and `ceiling_for` accepts `mode`.
- Evidence items accept `direct`, which the claim mode uses to decide whether an item bears
  on the claim.

## 0.2.0 — 2026-10-22

### Changed

- **No silent grade.** A claim with no `judgement.confidence` is refused (`no-grade`), and a
  grade above the evidence ceiling is refused (`grade-exceeds-evidence`); both exit 1.
- The tool imports `cti-method` directly. It no longer depends on `cryptonym`: the generic
  tool does not import the alias-specific one.
- `assess --against` re-derives the previous step's judgement and reports
  `judgement-mismatch` if the dossier changed after it was produced.
- `assess --register` verifies `requirement_id` against the PIR register.
- The ledger is append-only and **hash-chained** (`seq`, `created_at`, `prev_hash`,
  `claim_hash`, `hash`); `ledger --verify` reports the line that was edited.
- `weigh` requires at least two hypotheses; `calibrate` scores labelled calls generically.
- Docs moved into the package and ship with it.

- **Structural independence and weights**, shared with `cryptonym` through `cti-method`.
- `--now` writes a ledger entry at a fixed instant, so the same claim produces the same
  ledger; `--strict` validates the verdict against the published schema (exit 2 when it
  cannot).
- The verdict carries `$schema`, `favoured` and `inconsistency_scores`.


## 0.1.0 — 2026-10-22

First version published as a release. The repository has existed since 2026-10-09.

- First release: `assessment grade` (confidence and probability as separate axes), `assessment assess` over a document, and `assessment ledger`.
- Consumes the shared core from `cryptonym`; on `main` the core is mandatory (CI fails instead of skipping the core tests).
