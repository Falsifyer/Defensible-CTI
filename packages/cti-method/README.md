# cti-method

**The shared core of [cti-suite](https://github.com/ME0094/cti-suite/blob/main/README.md): one grade, one validator, one contract.**

Three things were being reimplemented six times, and drifting. They live here now.

| Module | What it owns | Who consumes it |
|---|---|---|
| `grading.py` | the **ceiling the evidence sets** on a declared confidence | `cryptonym`, `assessment` |
| `ach.py` | least-inconsistent ranking over arbitrary hypotheses | `cryptonym`, `assessment` |
| `adjudication.py` | external truth: standards, independence, contested | `cryptonym`, `assessment` |
| `stix.py` | **one** STIX 2.1 validator and the official TLP 2.0 markings | `stixforge`, `sharegate` |
| `contract.py` | findings, severities and the `0 / 1 / 2` exit codes | all six |
| `trace.py` | `requirement_id → assessment_id → hunt_id → report` | `huntplan`, `stixforge`, `cti-suite` |

## The grade ceiling

A declared confidence is a claim about the evidence, so the evidence caps it:

- **low** — no diagnostic item discriminates between the hypotheses (shared tradecraft
  cannot carry a grade above low, however much of it there is);
- **moderate** — at least one diagnostic item discriminates, all from one source;
- **high** — at least one diagnostic item discriminates **and** two independent sources
  contribute diagnostic evidence.

A grade below the ceiling is allowed (an analyst may be more cautious than the evidence).
A grade above it is `grade-exceeds-evidence`, a high finding: the tool refuses. A claim
that declares no grade at all is `no-grade`, also high — there is no silent default.

## One validator, one severity table

`validate_bundle()` is called by both the factory (`stixforge`) and the gate
(`sharegate`). Structural breakage, a missing marking, an unresolved reference, a
duplicate id or a wrong `spec_version` are high findings; an expired indicator, a bundle
with no marking definition or an unknown marking are medium; a deprecated `TLP:WHITE` is
low. The table is in one place so the two tools can no longer disagree.

The TLP markings are the OASIS TLP 2.0 objects
(`oasis-open/cti-stix-common-objects`), so `TLP:CLEAR` and `TLP:AMBER+STRICT` exist as
first-class labels and `TLP:WHITE` is recognised only to be flagged.

## Install

```console
$ uv sync --all-packages     # in the workspace
$ pip install -e packages/cti-method
```

No runtime dependencies: Python 3.11 or newer and the standard library.

## Licence

MIT. See [`../../LICENSE`](https://github.com/ME0094/cti-suite/blob/main/LICENSE).
