# Case 003 — LSASS access and dump file from Sysmon (real dataset)

> **Real data, public sample.** This is the other half of [case 002](case-002-lsass-minidump-4104.md): here
> the script content is missing and the execution is present. Read together, they show why one channel is
> never enough.

## 1. The dataset

| Field | Value |
|---|---|
| Source | [`sbousseaden/EVTX-ATTACK-SAMPLES`](https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES), `Credential Access/sysmon_10_11_lsass_memdump.evtx` |
| Size | 68 KB |
| SHA-256 | `915f0859251552b6c33efc32f6184d2c25419c5859852124a7f14ed6ec1a3723` |
| Events | **4** |
| Channel | `Microsoft-Windows-Sysmon/Operational` |
| Time span | **2019-03-17 19:09:41.328 → 19:10:03.991 UTC** (22.7 s) |
| Event IDs | **10 ×2** (process access), **11 ×2** (file create) |

## 2. What the events show

Two independent chains, 21 seconds apart, both opening LSASS with full access and writing a dump:

| Time | Source image | Target | Granted access | Dump file created |
|---|---|---|---|---|
| 19:09:41.328 | `C:\Users\IEUser\Desktop\procdump.exe` | `C:\Windows\system32\lsass.exe` | **`0x001FFFFF`** | `C:\Users\IEUser\Desktop\lsass.exe_190317_120941.dmp` |
| 19:10:02.068 | `C:\Windows\system32\taskmgr.exe` | `C:\Windows\system32\lsass.exe` | **`0x001FFFFF`** | `C:\Users\IEUser\AppData\Local\Temp\lsass (2).DMP` |

The call trace of both accesses passes through **`dbghelp.dll`** before returning to the calling image:

```
ntdll.dll → kernel32.dll → dbghelp.dll (×5) → procdump.exe / taskmgr.exe
```

That is the signature of the documented dump API (`MiniDumpWriteDump` lives in `dbghelp`), not of a
credential parser walking the process memory.

## 3. What this dataset proves — and what it does not

| Claim | Evidence here |
|---|---|
| LSASS was opened with full access | **yes**: EID 10, `0x001FFFFF`, twice |
| A dump file was written | **yes**: EID 11, `.dmp` in `Desktop` and `%TEMP%` |
| The tooling was signed / living off the land | **plausible**: `taskmgr.exe` is a signed Windows binary; `procdump.exe` is a Sysinternals tool — the sample does not include signatures or hashes |
| What the operator intended or ran before | **no**: no 4104, no EID 1, no user context |
| Whether the dump left the host | **no**: no network telemetry |

So the **opposite** gap to case 002:

- **case 002**: 4104 with `MiniDumpWriteDump` → intent proven, execution absent.
- **case 003**: Sysmon 10/11 → execution proven, intent (the script) absent.

**The method conclusion:** a hunt that only reads script-block logs will miss the dump; a hunt that only
reads Sysmon will miss the operator's code. Correlation by host and time is not a convenience — it is the
difference between «someone could» and «someone did».

## 4. Detection that follows

| Rule | Logic | Why |
|---|---|---|
| LSASS access | EID 10 where `TargetImage` ends with `\lsass.exe` and `GrantedAccess` is `0x1010` or `0x1FFFFF`, excluding an allowlist of EDR/backup agents by **hash** | access mask, not process name |
| Dump file | EID 11 where `TargetFilename` matches `*.dmp` under user-writable paths and `Image` is not an approved forensic tool | catches the artefact even if access is missed |
| Chain | both rules within 60 s on the same host | turns two medium signals into one high |

The `taskmgr.exe` path is the reason the first rule cannot be «procdump is bad»: a signed, built-in binary
can produce the same access. Allowlisting must be by hash and owner, not by name.

## 5. ATT&CK mapping

| ID | Technique | Evidence |
|---|---|---|
| **`T1003.001`** | OS Credential Dumping: LSASS Memory | EID 10 + EID 11, two chains |
| `T1218` | System Binary Proxy Execution | `taskmgr.exe` performing the dump *(supporting: signed binary, not proven proxy execution)* |

## 6. Limits

- **Lab sample** from 2019 (`IEUser` is an analysis VM account), not a production incident.
- **Four events**: no baseline, no prevalence, no fleet scope.
- No hashes, no signatures and no user SID in these events; the «living off the land» reading is an
  inference, and it is marked as such.
- The two chains may be independent tests rather than one operator; the dataset does not say.

---

Companion case: [case 002 — 4104 without Sysmon](case-002-lsass-minidump-4104.md) · Method: [`method.md`](method.md)
