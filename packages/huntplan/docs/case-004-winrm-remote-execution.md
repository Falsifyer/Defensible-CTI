# Case 004 — WinRM remote execution on a domain controller (real dataset)

> **Real data, public sample.** One event. That is the whole dataset, and the case is about what one event
> can support and what a pivot investigation must ask next — not about inventing the rest.

## 1. The dataset

| Field | Value |
|---|---|
| Source | [`sbousseaden/EVTX-ATTACK-SAMPLES`](https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES), `Lateral Movement/LM_PowershellRemoting_sysmon_1_wsmprovhost.evtx` |
| Size | 68 KB |
| SHA-256 | `c890d2b67dc2902b2fa5a094e517674920911a15b273f43c674fbfaa69540658` |
| Events | **1** |
| Channel | `Microsoft-Windows-Sysmon/Operational` |
| Event ID | **1** (process creation) |
| Host | `DC1.insecurebank.local` |
| Time | **2019-05-16 01:38:19.630 UTC** |

The single event:

| Field | Value |
|---|---|
| Image | `C:\Windows\System32\HOSTNAME.EXE` |
| ParentImage | **`C:\Windows\System32\wsmprovhost.exe`** |
| User | **`insecurebank\Administrator`** |
| CommandLine | `"C:\Windows\system32\HOSTNAME.EXE"` |

A second sample from the same folder (`LM_sysmon_remote_task_src_powershell.evtx`) was **not** merged into
this case: it is a different host (`MSEDGEWIN10`), a different year (2020-12-15) and only network events
(EID 3/7). Joining them would create a story the data does not tell.

## 2. What this event proves

- **Remote execution on `DC1`.** `wsmprovhost.exe` is the host process of PowerShell Remoting / WinRM. A
  child process coming from it was not started by a local console session.
- **The session ran as a domain administrator** (`insecurebank\Administrator`), not as a service account.
- **The command was reconnaissance**: `hostname.exe` is the cheapest way to confirm *which* machine the
  session landed on. It is the first command of a pivot, not the payload.

## 3. What it does not prove

| Missing | Why it matters |
|---|---|
| The **source host** | WinRM execution is defined by where the connection came from; this event has only the target |
| The **authentication** | `4624` logon type 3 with the account, or WinRM operational `91`/`168`, would show the logon and the client IP |
| The **rest of the session** | Only one child process is recorded; the operator may have run ten more |
| **Persistence or staging** | No file, service or scheduled task in the sample |

One Sysmon 1 event is a **lead**, not a pivot. Calling it «lateral movement across hosts» from this dataset
would be the same error as calling a 4104 «LSASS dumped».

## 4. The pivot investigation this event demands

Ordered by cost, not by tool:

1. **Source address.** On `DC1`, look for Security `4624` (logon type 3) with `insecurebank\Administrator`
   in `±60 s`, and WinRM operational `91` (session created) / `168`. The `IpAddress` field is the pivot
   point.
2. **Name that address.** Resolve it with DHCP leases (Pi-hole/DHCP) or DNS, not by guessing. If it is a
   workstation, the operator used a valid admin account from there; if it is another server, the pivot is
   already a chain.
3. **On the source host.** Sysmon 1 for `powershell.exe` with `Enter-PSSession`/`Invoke-Command`, `4104`
   for the client-side script block, and `4688`/`4624` for the local session that launched it.
4. **Same account, other hosts.** A single `4624` type 3 for that account on `DC1` is a data point; the
   same account authenticating to several hosts in a short window is the hunt.
5. **What ran next.** `hostname.exe` proves landing; the next child processes on `DC1` (and their 4104, if
   PowerShell) are the actual objective.

## 5. Detection

| Rule | Logic | Note |
|---|---|---|
| Remote shell child | Sysmon 1 where `ParentImage` ends with `\wsmprovhost.exe` and the child is `cmd.exe`, `powershell.exe`, `hostname.exe`, `whoami.exe`, `ipconfig.exe`, `net.exe` | baseline first: some admin scripts legitimately use WinRM |
| Remote logon to a DC | Security 4624 type 3 on a domain controller with a privileged account, outside a maintenance window | requires knowing the maintenance window; without it, the rule is noise |
| Admin session anomaly | 4624 type 3 for the same privileged account on `≥3` hosts in `≤10 min` | the pivot signature, not the single hop |

## 6. ATT&CK mapping

| ID | Technique | Evidence |
|---|---|---|
| **`T1021.006`** | Remote Services: Windows Remote Management | `wsmprovhost.exe` as parent |
| **`T1018`** | Remote System Discovery | `hostname.exe` as the executed command |
| **`T1078.002`** | Valid Accounts: Domain Accounts | `insecurebank\Administrator` used interactively over WinRM |

`T1059.001` (PowerShell) is the **transport**, not the observed child: the event shows `hostname.exe`, so it
is not claimed here. If the 4104 of the session existed, it would be the evidence for it.

## 7. Limits

- **One event, one host, one second**: no baseline, no prevalence, no chain.
- Lab domain (`insecurebank.local`), 2019; not a production incident.
- No `Computer`/`User` SID, hashes or signature data beyond the fields above.
- The «first command of a pivot» reading is an **inference from the command chosen**, and it is marked as
  such.

---

Companions: [case 002](case-002-lsass-minidump-4104.md) · [case 003](case-003-lsass-sysmon-access-dump.md) · Method: [`method.md`](method.md)
