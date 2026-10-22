# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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


## 0.1.0 — 2026-10-22

First version published as a release. The repository has existed since 2026-10-09.

- First release: `assessment grade` (confidence and probability as separate axes), `assessment assess` over a document, and `assessment ledger`.
- Consumes the shared core from `cryptonym`; on `main` the core is mandatory (CI fails instead of skipping the core tests).
