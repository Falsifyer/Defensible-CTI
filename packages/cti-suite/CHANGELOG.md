# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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

