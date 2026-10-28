# HuntPlan

**Turn a question into a falsifiable threat-hunting plan.**

> A hunt starts from a hypothesis, not from a tool.

HuntPlan forces the discipline that separates hunting from browsing:

- a **falsifiable hypothesis** (*If … then …*), not a vague intent;
- the **ATT&CK detection strategies** that would satisfy it, with their analytics and data
  components (a curated subset; ATT&CK v18 deprecated Data Sources);
- a **closure criterion** — when the hunt is done, and what "not found" means;
- a **maturity** assessment against the Hunting Maturity Model (HMM 0→4);
- the **assessment it answers**, verified against the upstream file.

## Example

A hypothesis that cannot be refuted is rejected, and the CLI says why (exit code 1):

```console
$ echo "The actor is probably active somewhere" > h.txt
$ huntplan validate h.txt
{
  "falsifiable": false,
  "findings": [
    {"code": "not-falsifiable", "severity": "high", "message": "State it as 'If <condition> then <observable>'"},
    {"code": "no-observable", "severity": "high", "message": "Name the telemetry that would show the condition (a log, an event, a record)"}
  ]
}

$ echo "If the actor uses scheduled tasks to stage the loader, then process creation logs will show schtasks.exe with a /create argument" > h.txt
$ huntplan validate h.txt
{"falsifiable": true, "findings": []}
```

A **sentence that merely contains both words** is not a hypothesis: they have to be the
structure (`^If|When … then …`), and the observable has to be named.

A ready plan names the technique, its detection strategies and the closure criterion:

```console
$ huntplan validate demo/hunt.json --assessment out/verdict.json
```

```json
{
  "id": "HUNT-001",
  "assessment_id": "nightjar-vs-saltwind",
  "ready": true,
  "techniques": [
    {"technique_id": "T1053", "known": true,
     "detection_strategies": [{"id": "DET0094", "name": "...", "analytics": [...]}],
     "data_components": ["Scheduled Job", "Process Creation"]}
  ],
  "attack": {"collection": "Enterprise ATT&CK", "attack_version": "20.0"}
}
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

## ATT&CK v18+

ATT&CK **deprecated Data Sources in v18 (October 2025)** and replaced the detection mapping
with **Detection Strategies** and **Analytics** that reference **Data Components**. The map
shipped here is generated from the Enterprise ATT&CK STIX collection — currently 20.0,
modified 2026-10-13 — and committed with its provenance:

```console
$ python scripts/build_attack_map.py --stix enterprise-attack.json
$ huntplan sources T1059          # 14 detection strategies, with platforms and log channels
```

The subset is 12 techniques and says so: an unknown technique is reported as unknown,
never guessed at.

## What it is not

- **Not a SIEM or a query engine.** It plans; you run.
- **Not a detector.** A confirmed hunt becomes a detection elsewhere.
- **Not a full ATT&CK database.** The subset is curated and small, and the output says so.

## Install and use

```bash
pip install -e ../cti-method -e '.[mcp]'
huntplan hmm
huntplan validate hypothesis.txt     # exit 1 if not falsifiable
huntplan validate plan.json --assessment verdict.json
huntplan sources T1059
```

## As an MCP server

```bash
huntplan-mcp
```

Tools: `hmm_levels_table`, `validate_hypothesis_text`, `detection_strategies_for_technique`,
`data_sources_for_technique` (deprecated alias), `attack_map_provenance`, `assess_maturity`,
`build_plan`, `validate_plan_document`.

## Method

See [docs/method.md](docs/method.md).

## License

MIT — see [LICENSE](https://github.com/Falsifyer/Defensible-CTI/blob/main/LICENSE).

---

**Martín Eliseo** — cyber threat intelligence.
[GitHub](https://github.com/Falsifyer) · [falsifyer.github.io](https://falsifyer.github.io)
