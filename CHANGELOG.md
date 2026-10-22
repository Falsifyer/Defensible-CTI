# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

Versions are per package; each package keeps its own `CHANGELOG.md` with its detail.

## 0.1.0 — 2026-10-22

- First version of the workspace: the six tools move here from their own repositories, unchanged in
  name, command and behaviour.
- `assessment` now depends on `cryptonym` through the workspace, so its CI no longer needs a personal
  access token to install the core.
- `make demo` runs the six in order on fictional data: requirement, judgement, ledger, hunt plan,
  STIX product and gate.
