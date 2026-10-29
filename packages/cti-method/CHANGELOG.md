# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## Unreleased

### Fixed

- **ACH counts voices, not items.** `inconsistency_scores` groups by publisher (or
  normalised source string), so restating one source cannot flip the ranking.
- **Ties are surfaced, not broken by input order.** `tied_at_top` names the hypotheses the
  evidence does not separate; the count also counts voices, not restated items.
- **An unaddressed hypothesis does not win by silence.** A hypothesis no item addresses is
  ranked after the tested ones instead of tying them at zero inconsistency.
- **Positive diagnostic support is required.** `supported_hypotheses` names the hypotheses
  with at least one `infrastructure`/`code`/`operator` item consistent with them; a
  hypothesis with only linguistic/structural consistency is `consistent_but_unsupported`.
- **Identity contradictions outrank context.** The ranking is
  `addressed > supported > identity inconsistency > context inconsistency > voices`;
  `ranking_basis` exposes the data behind that order.
- **Shared tradecraft cannot undo a contradiction downgrade.** Only discriminating items
  count as support in the ceiling's contradiction step.
- **A document too deep for the JSON parser is `CannotCheck`**, not a `RecursionError`.
- **Every content SDO needs a marking.** The whitelist exempted `infrastructure`, `note`,
  `attack-pattern` and `relationship`; only SCOs and structural definitions are exempt now.
- **Schema `$id`/`$schema` resolve** to the raw URL of the shipped file (the old `/schemas/`
  path returned 404).

## 0.2.0 — 2026-10-28

### Added

- **Claim mode for the ceiling.** `ceiling(..., mode="claim")` grades a statement that has
  no competing hypotheses — a factual claim — by whether an item bears **directly** on it
  (`Evidence.direct`), with the same structural independence rule and no contradiction
  step. Without it, every factual claim was capped at `low` because
  `is_discriminating()` is false when there is no hypothesis to differ from.
- **`policy()`**: the grading policy as data — both modes, their thresholds and the
  independence rule — so a consumer renders the standard instead of restating it.
- `EvidenceProfile.mode` and `.direct`, so a result says which mode produced it.

### Changed

- `profile`, `ceiling`, `derived_grade` and `check_declared` take `mode` (default `ach`,
  behaviour unchanged).
- The ACH mode is untouched: `direct` defaults to `false` and is ignored unless the mode
  asks for it.

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

