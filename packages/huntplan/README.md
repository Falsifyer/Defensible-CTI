# HuntPlan

**Turn a question into a falsifiable threat-hunting plan.**

[![CI](https://github.com/ME0094/huntplan/actions/workflows/ci.yml/badge.svg)](https://github.com/ME0094/huntplan/actions/workflows/ci.yml)

> A hunt starts from a hypothesis, not from a tool.

HuntPlan forces the discipline that separates hunting from browsing:

- a **falsifiable hypothesis** (*If … then …*), not a vague intent;
- the **ATT&CK data sources** that would satisfy it (a curated subset; the ATT&CK MCP has
  the full mapping);
- a **closure criterion** — when the hunt is done, and what "not found" means;
- a **maturity** assessment against the Hunting Maturity Model (HMM 0→4).

## Example

A hypothesis that cannot be refuted is rejected, and the CLI says why (exit code 1):

```console
$ echo "The actor is probably active somewhere" > h.txt
$ huntplan validate h.txt
{
  "falsifiable": false,
  "findings": [
    {"code": "not-falsifiable", "severity": "high", "message": "State it as 'If <condition> then <observable>'"},
    {"code": "no-data-source", "severity": "medium", "message": "Name the telemetry that would satisfy the hypothesis"}
  ]
}

$ echo "If the actor uses scheduled tasks, then process creation logs will show schtasks.exe with a /create argument" > h.txt
$ huntplan validate h.txt
{"falsifiable": true, "findings": []}
```

A ready plan names the technique, its telemetry and the closure criterion:

```console
$ huntplan sources T1059
{
  "technique_id": "T1059",
  "known": true,
  "technique": "Command and Scripting Interpreter",
  "sources": ["Process creation (command line)", "Script block logging", "Module load"]
}
```

```python
>>> build_hunt_plan(
...     question="Has actor X moved laterally?",
...     hypothesis="If actor X moves laterally, then authentication logs will show NTLM logons to multiple hosts",
...     techniques=["T1021", "T1078"],
...     closure="Confirmed if two or more hosts show the pattern; refuted if no such logons exist over 30 days",
... )
{"ready": true, "gaps": [],
 "techniques": [{"technique_id": "T1021", "known": true,
                 "sources": ["Authentication logs", "Network traffic", "Process creation"]}, ...]}
```

Four worked cases:

- [`docs/case-004-winrm-remote-execution.md`](docs/case-004-winrm-remote-execution.md) — **real public
  dataset** (1 event): `wsmprovhost.exe` as parent on a domain controller, and the pivot investigation that
  one event demands.
- [`docs/case-002-lsass-minidump-4104.md`](docs/case-002-lsass-minidump-4104.md) — **real public dataset**
  (4 events, one channel): an LSASS minidump visible in a PowerShell 4104, and what that log proves and
  does not prove.
- [`docs/case-003-lsass-sysmon-access-dump.md`](docs/case-003-lsass-sysmon-access-dump.md) — **real public
  dataset** (4 events, Sysmon): the same technique seen from process access and file creation. Read with
  case 002, it shows why one channel is never enough.
- [`docs/case-001-powershell-cradle.md`](docs/case-001-powershell-cradle.md) — **simulated** end-to-end
  case: a download cradle from a document, its telemetry, findings and closure.

## What it is not

- **Not a SIEM or a query engine.** It plans; you run.
- **Not a detector.** A confirmed hunt becomes a detection elsewhere.
- **Not a full ATT&CK data-source database.** The subset is curated and small, and says so.

## Install and use

```bash
pip install -e '.[mcp]'
huntplan hmm
huntplan validate hypothesis.txt     # exit 1 if not falsifiable
huntplan sources T1059
```

## As an MCP server

```bash
huntplan-mcp
```

Tools: `hmm_levels_table`, `validate_hypothesis_text`, `data_sources_for_technique`,
`assess_maturity`, `build_plan`.

## Method

See [docs/method.md](docs/method.md).

## License

MIT — see [LICENSE](LICENSE).

---

**Martín Eliseo** — cyber threat intelligence.
