# Changelog

## Unreleased

### Fixed

- **Ties are surfaced** in `assess` and `render` (`tied`, `favoured: null`) instead of
  being resolved by the order of the hypothesis list.
- **The ACH ranking counts voices**, so a source restated twice cannot flip it.
- **The evaluation does not score a tie by list order.** `tied`/`abstained` are reported;
  a tie that includes `same_actor` is an abstention, not a call. The golden and adjudicated
  baselines were regenerated.
- **The MCP `snapshot_source` tool cannot be told to reach a private address**: the
  `allow_private` opt-out is CLI-only, not an agent argument.

## 0.7.0 — 2026-10-22

### Changed

- **The grade is checked against the evidence.** `assess` now reports the ceiling the
  evidence supports and a `grade-exceeds-evidence` high finding when the dossier claims
  more; the CLI exits 1 in that case. A dossier with no declared grade is `no-grade`, not a
  silent `low`.
- The graded core moved to `cti-method`; `cryptonym.method` and the `model`/`assess`/
  `evaluate` modules re-export it. The alias package is a consumer of the core, not its
  owner.
- Default TLP is `TLP:CLEAR` (TLP 2.0), not the deprecated `TLP:WHITE`.
- Documentation ships inside the installed package, so the MCP `documentation` tool works
  from a wheel.
- Calibration in the evaluation harness is computed on the derived ceiling, not on the
  declared grade.

- **Structural independence and weights**: the dossier registers its sources and evidence
  points at them; ACH ranks by Admiralty-weighted inconsistency; evidence that contradicts
  the favoured hypothesis lowers the ceiling.
- **Probability calibration** on the estimative axis (Brier score), reported per split.
- **The STIX export is marked** with the official TLP 2.0 object and validated by the
  suite's validator, so it can be gated by `sharegate` instead of travelling unmarked.
- The shipped worked example uses `TLP:CLEAR` (TLP 2.0) instead of the deprecated alias.


## 0.6.0 — 2026-10-09

- **Generalised ACH:** `consistency_matrix`, `inconsistency_counts` and
  `least_inconsistent` now accept arbitrary hypothesis labels, not only the actor
  taxonomy — so the shared core can grade any question, not just aliases.

## 0.5.0 — 2026-10-09

- **Renamed Concord → Cryptonym.** A cryptonym is the cover name given to an actor; the
  tool decides whether two of them are the same actor. Package, CLI, STIX custom objects,
  docs and tests renamed; repository renamed to `Falsifyer/cryptonym`.
- **`cryptonym.method`:** the shared, stable assessment core, extracted as a public
  surface every family tool imports instead of reimplementing. See `docs/method-api.md`.

## 0.4.0 — 2026-10-09

- **MCP server** (`cryptonym.mcp_server`): the reconciliation method exposed as MCP tools
  (assess, render, export, ingest, adjudicate, reconcile, snapshot, documentation) over
  stdio. Entry point `cryptonym-mcp`; optional extra `.[mcp]`. See `docs/mcp.md`.

## 0.3.0 — 2026-10-09

External adjudication (the next milestone after M9).

- **`cryptonym.evaluate.adjudication`:** the external-truth filter. Truth vocabulary
  (`same_actor` / `distinct` / `contested` / `unadjudicated`), evidence standards
  (`author-assertion` … `independent-corroboration`), an independence rule (same
  publisher or derived sources count once), and a disagreement policy (hard conflict →
  contested; scope dissent downgrades an uncorroborated claim).
- **Adjudicated corpus:** `evaluation/adjudicated/` with a schema, a real-source seed
  (CISA AA23-320A, MITRE G1015/G0007/G0032, Microsoft, Google) and a committed coverage
  baseline. Coverage and standards are reported alongside the metrics.
- **`evaluate_adjudicated`:** only admissible binary truths enter the error rates;
  contested and unadjudicated cases are reported as coverage.
- **CLI:** `cryptonym adjudicate --strict`; `run_evaluation.py --adjudicated --check
  --strict` in CI.

## 0.2.0 — 2026-10-09

Milestones M7, M8 and M9.

- **Snapshots (M7):** `cryptonym.snapshot` captures a source's bytes and SHA-256 so a
  judgement can be re-derived against the exact document it was built from; the CLI
  gains `snapshot --source/--verify`.
- **Held-out evaluation (M8):** the corpus now carries a `development` / `held-out`
  split; `cryptonym.evaluate.evaluate_corpus` reports the confusion matrix and
  calibration **per split**, and `--check` fails on drift.
- **Network fetch (M9):** `cryptonym.ingest.fetch` fetches source JSON from an
  SSRF-validated endpoint (HTTPS enforced, size cap, JSON only). Network access stays
  out of the core and is delegated to an injected fetcher for testing; the CLI gains
  `ingest --url`.
- Repository made public.

## 0.1.0 — 2026-10-09

Milestones M2, M4, M5 and M6.

- **Ingest (M2):** MISP Galaxy, MITRE ATT&CK (STIX) and OpenCTI adapters. Offline and
  dict-based; each keeps a source's names **apart** as separate designations.
- **Export (M4):** STIX 2.1 bundle, MISP Galaxy cluster (`assessed_not_asserted`) and
  TAXII 2.1 envelope. STIX is emitted as JSON and validated against the official `stix2`
  library in CI.
- **Evaluation (M5):** `cryptonym.evaluate` — confusion, false-merge / false-split rates
  and a calibration table; a golden-pair corpus with a committed baseline and a CI
  `--check`.
- **CLI:** `ingest` added; `export --format stix|misp|taxii`.
- **Release (M6):** version bump and release tag.

## 0.0.1 — 2026-10-09

- Initial skeleton: data model, two-axis grading, ACH engine, graded reconciliation
  graph, markdown product, security boundary.
- Worked example: `assessments/voltzite-vs-volt-typhoon/`.
- CI: ruff, bandit, pip-audit, pytest with branch coverage on 3.11–3.13, plus a
  reproducibility check on the worked example.
