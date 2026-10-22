# Case 002 — LSASS minidump from a PowerShell script block (real dataset)

> **Real data, public sample.** Not a simulation: the events come from a published attack sample. What the
> sample does **not** contain is as important as what it does, and the case states both.

## 1. The dataset

| Field | Value |
|---|---|
| Source | [`sbousseaden/EVTX-ATTACK-SAMPLES`](https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES), `Credential Access/Powershell_4104_MiniDumpWriteDump_Lsass.evtx` |
| Size | 68 KB |
| SHA-256 | `54ff62eff26af588782e066b7b3b1b952bc83e1b75a84d81f9492e654cb5c319` |
| Events | **4** |
| Channel | `Microsoft-Windows-PowerShell/Operational` |
| Time span | **2020-06-30 14:23:58.394 → 14:24:08.254 UTC** (10.1 s) |
| Event IDs | `40961` ×1, `53504` ×1, `40962` ×1, **`4104` ×1** |

Reproduce:

```bash
curl -fsSL "https://raw.githubusercontent.com/sbousseaden/EVTX-ATTACK-SAMPLES/master/Credential%20Access/Powershell_4104_MiniDumpWriteDump_Lsass.evtx" -o ps_lsass.evtx
sha256sum ps_lsass.evtx
uv run --with python-evtx python parse.py ps_lsass.evtx
```

## 2. The hypothesis

> **If** an operator dumps LSASS from PowerShell, **then** the script block log will contain a call chain
> that obtains a handle to `lsass`, invokes the Windows Error Reporting `MiniDumpWriteDump` routine, and
> writes a `.dmp` file — **and** the endpoint telemetry will show the process access and the file creation.

The first half is testable on this dataset. The second half is **not**: the sample contains only one
channel. That is the point of the case.

## 3. What the 4104 actually says

The single script block (1 488 characters, `MessageNumber 1/1`, `ScriptBlockId 27f08bda-…`) defines:

```powershell
$Process = Get-Process lsass
$WER  = [PSObject].Assembly.GetType('System.Management.Automation.WindowsErrorReporting')
$WERNativeMethods = $WER.GetNestedType('NativeMethods','NonPublic')
$MiniDumpWriteDump = $WERNativeMethods.GetMethod('MiniDumpWriteDump', $flags)
$MiniDumpWithFullMemory = [UInt32] 2
$FileStream = New-Object IO.FileStream($ProcessDumpPath, [IO.FileMode]::Create)
$Result = $MiniDumpWriteDump.Invoke($null, @($ProcessHandle, $ProcessId, $FileStream.SafeFileHandle, 2, ...))
```

Key facts it establishes, without inference:

- the target is **`lsass`** (`Get-Process lsass`);
- the API is **`MiniDumpWriteDump`**, reached by reflection through `WindowsErrorReporting` to avoid a
  direct P/Invoke signature;
- the dump type is **`MiniDumpWithFullMemory` (0x2)**, i.e. full memory, not a minidump;
- the script was executed **from a file**: `Path = C:\Users\Public\lsass_wer_ps.ps1`.

## 4. What the dataset does not contain

| Missing telemetry | Why it matters |
|---|---|
| Sysmon **10** (process access) | would show `lsass.exe` being opened with `0x1010`/`0x1FFFFF` by `powershell.exe` |
| Sysmon **11** (file create) | would show `lsass.dmp` appearing on disk |
| Sysmon **1** (process creation) | would show the parent, the command line and the user |
| Security **4688** / **4663** | fallback for process creation and object access if Sysmon is absent |
| Security **4624** | the identity under which the dump ran |

Consequence: **the sample proves intent and capability, not execution.** A 4104 alone is not a compromise;
it is a script that was compiled and logged. Claiming «LSASS was dumped» from these four events would be
exactly the mistake this method exists to prevent.

## 5. ATT&CK mapping

| ID | Technique | Evidence in the sample |
|---|---|---|
| **`T1003.001`** | OS Credential Dumping: LSASS Memory | `Get-Process lsass` + `MiniDumpWriteDump` + `MiniDumpWithFullMemory` |
| **`T1059.001`** | PowerShell | the script block itself (4104) |
| `T1027` | Obfuscated Files or Information | reflection to reach a private .NET type instead of a direct API import *(supporting, not proven intent)* |

## 6. Decision and closure

| Output | Condition | What this dataset allows |
|---|---|---|
| **Intent confirmed** | 4104 shows LSASS + `MiniDumpWriteDump` + full-memory flag | **yes** — it is in the log |
| **Execution confirmed** | the dump file exists and the process access is recorded | **no** — telemetry absent |
| **Refuted** | no such script block and no process access over the window, with measured coverage | **cannot be evaluated** — no coverage data in a one-channel sample |
| **Visibility gap** | 4104 present but Sysmon 10/11 absent | **this is the correct output** for this dataset |

The honest close is: *a script capable of dumping LSASS was executed from `C:\Users\Public`; whether the dump
succeeded cannot be established from these events, and the absence of process-access telemetry is the first
gap to close.*

## 7. Limits

- **Public lab sample**, generated in 2020 by the dataset author; it is real telemetry, not a real incident.
- **One host, one channel, 10 seconds**: no baseline, no prevalence, no fleet scope.
- Windows 10-era event schema: field names and defaults may differ in current builds.
- The script itself is malicious by intent; it is quoted only as evidence, not as tooling.
