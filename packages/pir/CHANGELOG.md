# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## 0.1.0 — 2026-10-22

- `pir validate`: rejects a register with a requirement lacking a decision, lacking a consumer, or
  with ungraded indicators; warns about questions that are not questions, out-of-scale priorities,
  deadlines in the past and duplicate identifiers.
- `pir list`: requirements with their decision, their deadline and the days left.
- Rules `no-decision`, `no-consumer`, `no-question`, `not-a-question`, `bad-priority`,
  `bad-deadline`, `stale`, `no-eei`, `eei-no-question`, `eei-no-indicator`, `indicator-no-value`,
  `indicator-ungraded`, `bad-admiralty`, `duplicate-id`, `malformed`.
