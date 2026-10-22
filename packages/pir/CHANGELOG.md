# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## 0.2.0 — 2026-10-22

### Added

- **An MCP server** (`pir-mcp`): the first step of the cycle was the only one an agent could
  not reach.
- `pir ids` prints the requirement identifiers the rest of the cycle cites.
- `schema_version` and a register `id` in the format; the schema is published in `schemas/`.

### Changed

- Findings use the shared shape (`code`, `severity`, `message`, `where`).
- An unreadable or invalid file exits **2**; a high finding exits 1.

- Findings are in English, like the rest of the CLI surface.


## 0.1.0 — 2026-10-22

- `pir validate`: rejects a register with a requirement lacking a decision, lacking a consumer, or
  with ungraded indicators; warns about questions that are not questions, out-of-scale priorities,
  deadlines in the past and duplicate identifiers.
- `pir list`: requirements with their decision, their deadline and the days left.
- Rules `no-decision`, `no-consumer`, `no-question`, `not-a-question`, `bad-priority`,
  `bad-deadline`, `stale`, `no-eei`, `eei-no-question`, `eei-no-indicator`, `indicator-no-value`,
  `indicator-ungraded`, `bad-admiralty`, `duplicate-id`, `malformed`.
