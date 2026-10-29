# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## Unreleased

### Fixed

- **`--out` no longer deletes an arbitrary directory.** A target that contains the inputs,
  the working directory or the home directory is refused; a non-empty explicit target needs
  `--force`.
- **The report renders a tie** instead of choosing the first hypothesis as the winner.
- **The chain anchors its ledger**: the append writes `ledger.head` and the verify step
  checks it, so a truncated tail fails the demo.
- **The release workflow is split**: build has `contents: read`; only the download/sign/
  publish job gets `contents: write` + `id-token: write`. All actions are pinned to commits.
- **The publishing runbook names `Defensible-CTI`**, not the old `cti-suite` repository.
- **The default environment is `pip check` clean**: the `opencti` extra is opt-in, because
  pycti's pins conflict with the security overrides.

## 0.1.0 — 2026-10-22

- First version. `ctisuite report` renders requirement, judgement, evidence, hunt plan and
  marking as one markdown product; `ctisuite-mcp` is one MCP facade for the six tools.
- The integration tests live here: the six exit codes, the one-validator guarantee, the demo
  chain, the schemas and the version drift.

- **`ctisuite chain --dir`** runs the seven steps through the real entry points and returns
  one exit code; `demo/run.sh` is now a wrapper around it.
- **BLUF**: the report opens with what is claimed, the declared grade, the ceiling, why and
  what would change it, all read from the judgement.
- `report --require-complete` exits 1 when a link of the chain is missing.
- The tag → package mapping moved to `cti_suite.release`, with tests.

