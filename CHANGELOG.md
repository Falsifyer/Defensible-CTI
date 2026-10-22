# Changelog

The workspace has no version of its own. Each package keeps its own `CHANGELOG.md` and its
own tag:

| Package | Version | Changelog |
|---|---|---|
| `cti-method` | 0.1.0 | [packages/cti-method/CHANGELOG.md](packages/cti-method/CHANGELOG.md) |
| `cryptonym` | 0.7.0 | [packages/cryptonym/CHANGELOG.md](packages/cryptonym/CHANGELOG.md) |
| `assessment-mcp` | 0.2.0 | [packages/assessment/CHANGELOG.md](packages/assessment/CHANGELOG.md) |
| `sharegate` | 0.2.0 | [packages/sharegate/CHANGELOG.md](packages/sharegate/CHANGELOG.md) |
| `stix-forge` | 0.2.0 | [packages/stixforge/CHANGELOG.md](packages/stixforge/CHANGELOG.md) |
| `pir-ledger` | 0.2.0 | [packages/pir/CHANGELOG.md](packages/pir/CHANGELOG.md) |
| `huntplan` | 0.2.0 | [packages/huntplan/CHANGELOG.md](packages/huntplan/CHANGELOG.md) |
| `cti-suite` | 0.1.0 | [packages/cti-suite/CHANGELOG.md](packages/cti-suite/CHANGELOG.md) |

## 2026-10-22 — the cycle becomes a chain

- **`cti-method` 0.1.0** — the shared core: the evidence-derived ceiling, one STIX 2.1
  validator, the `0/1/2` contract and the artifact trace. `cryptonym` is now a consumer of
  the core instead of its owner, and `assessment` no longer imports the alias package.
- **`cryptonym` 0.7.0** — the declared grade is checked against the ceiling
  (`grade-exceeds-evidence`); `cryptonym assess` exits 1 when the dossier claims more than
  the evidence supports. TLP 2.0 by default. Docs moved into the package.
- **`assessment-mcp` 0.2.0** — no silent default grade, `--against` re-derives the previous
  step's judgement, the ledger is hash-chained and verifiable, docs ship with the package.
- **`stixforge` 0.2.0** — official TLP 2.0 markings, `created` required, trace ids emitted as
  `external_references`, the factory validates what it builds.
- **`sharegate` 0.2.0** — one validator (imported, not reimplemented), markings resolved from
  `object_marking_refs`, the sensitive-content heuristic is a medium guard, exit 2 on
  unreadable input.
- **`huntplan` 0.2.0** — ATT&CK 20.0 detection strategies (Data Sources were deprecated in
  v18), stricter falsifiability, JSON plans with trace.
- **`pir-ledger` 0.2.0** — an MCP server (the first step was the only one an agent could not
  reach), `pir ids`, `schema_version`, exit 2 on unreadable input.
- **`cti-suite` 0.1.0** — `ctisuite report` and the `ctisuite-mcp` facade.
- The demo now chains: each step consumes the previous output and verifies the id.
- **Sources are structural**: a dossier registers its sources (`id`, `publisher`,
  `derived_from`, `reliability`) and the ceiling counts independent voices, not strings.
- **ACH is weighted** by the Admiralty band, and evidence that contradicts the favoured
  hypothesis lowers the ceiling.
- **The probability axis is scored**: Brier score and per-band reliability alongside
  confidence calibration; the corpus now has a `high` band (11 held-out cases) and reports
  0 declared above the ceiling.
- **The trace pins content**: `<kind>_hash` is verified and `<id>@<sha256:12>` travels in
  the STIX references.
- **Limits**: 8 MiB / 64 levels on input, 20,000 objects on a bundle, exit 2.
- **`ctisuite chain`** runs the seven steps in code; `demo/run.sh` wraps it.
- **BLUF** in the report, `--require-complete`, `sharegate --today`, ledger `--now`,
  `--strict` against the published schemas, English findings in `pir`.
- **Engineering**: external STIX validation in CI, property tests for the ceiling, pip-audit
  with one documented exception, actionlint/shellcheck, a testable tag→package mapping,
  signed releases and a trusted-publishing workflow.
