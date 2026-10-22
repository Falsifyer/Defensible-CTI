# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- **`docs/case-004-winrm-remote-execution.md`**: one real Sysmon event — `wsmprovhost.exe` spawning
  `hostname.exe` on a domain controller as a domain administrator. It states what one event proves, what it
  cannot, and the ordered pivot investigation it demands (4624 type 3, WinRM 91/168, source host, same
  account across hosts).
- **`docs/case-003-lsass-sysmon-access-dump.md`**: the complement of case 002 on real Sysmon data —
  `EID 10` with `GrantedAccess 0x001FFFFF` and `EID 11` writing `.dmp` files, twice in 22.7 s. Execution is
  proven; the script is absent, which is exactly the gap case 002 leaves.
- **`docs/case-002-lsass-minidump-4104.md`**: analysis of a real public EVTX sample (4 events, 10.1 s,
  one channel). It shows a `MiniDumpWriteDump` LSASS dump in a PowerShell 4104 and, explicitly, why the
  sample cannot prove execution — the visibility gap is the output, not a finding.

### Changed

- Replaced the earlier case document with a **simulated hunt case**
  ([`docs/case-001-powershell-cradle.md`](docs/case-001-powershell-cradle.md)): alert, hypothesis, minimum
  telemetry, findings with synthetic values, ATT&CK mapping, closure and stated limits.

## [0.1.0] — 2026-10-19

### Added

- **Falsifiable hypothesis validation** (`validate_hypothesis`): rejects statements that are not
  *If … then …*, that name no telemetry, that hedge (`might`, `could`) or that are too short to test.
- **Curated ATT&CK data-source subset** for ten techniques (`T1059`, `T1003`, `T1055`, `T1071`,
  `T1105`, `T1547`, `T1053`, `T1112`, `T1021`, `T1078`), reporting absence instead of guessing.
- **Closure criteria and plan assembly** (`build_hunt_plan`): a plan is *ready* only with a falsifiable
  hypothesis, at least one technique and an explicit closure.
- **Hunting Maturity Model** levels 0–4 and `assess_hunt_maturity`, where each rung requires the one
  below it.
- **CLI** (`huntplan validate|sources|hmm`) and **MCP server** (`huntplan-mcp`) with five tools.

### Documentation

- README worked example with real CLI and library output, and the CI badge.
- A worked case document (superseded in *Unreleased* by the simulated case 001), stating its minimum
  telemetry and its closure criteria with the limits visible.

### Quality

- 12 tests with **95 % branch coverage** (gate at 80 %).
- CI: blocking `ruff`, `bandit`, and a test matrix on Python 3.11, 3.12 and 3.13.
