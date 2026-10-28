# cti-method

**The shared core of [cti-suite](../../README.md): one grade, one validator, one contract.**

Three things were being reimplemented six times, and drifting. They live here now.

| Module | What it owns | Who consumes it |
|---|---|---|
| `grading.py` | the **ceiling the evidence sets** on a declared confidence, from independent sources and the contradiction in the evidence | `cryptonym`, `assessment` |
| `sources.py` | the dossier's source registry: who said it, who repeats whom, which band | `cryptonym`, `assessment` |
| `ach.py` | least-inconsistent ranking over arbitrary hypotheses, weighted by Admiralty reliability | `cryptonym`, `assessment` |
| `adjudication.py` | external truth: standards, independence, contested | `cryptonym`, `assessment` |
| `metrics.py` | confusion, confidence calibration, **probability calibration (Brier)** | `cryptonym`, `assessment` |
| `stix.py` | **one** STIX 2.1 validator, size limits and the official TLP 2.0 markings | `stixforge`, `sharegate` |
| `contract.py` | findings, severities, `0 / 1 / 2`, and the byte/depth limits | all six |
| `trace.py` | `requirement_id → assessment_id → hunt_id`, with the **hash of the content** | `huntplan`, `stixforge`, `cti-suite` |
| `schema.py` | the published schemas, available from the installed package | `assessment`, `cryptonym`, CI |

## The grade ceiling

A declared confidence is a claim about the evidence, so the evidence caps it:

- **low** — no diagnostic item discriminates between the hypotheses (shared tradecraft
  cannot carry a grade above low, however much of it there is);
- **moderate** — at least one diagnostic item discriminates, all from one independent source;
- **high** — at least one diagnostic item discriminates **and** two independent sources
  contribute diagnostic evidence.

Independence is **structural**, not typographic: a dossier registers its sources
(`sources: [{id, publisher, derived_from, reliability}]`) and evidence points at them with
`source_id`. Two reports from one publisher are one voice; a source that derives from
another present is not a second voice. Without a registry the engine falls back to the
source string and says so in the reasons.

The ceiling drops one step when the diagnostic evidence that **contradicts** the favoured
hypothesis outweighs the diagnostic evidence that supports it: density is not direction.

A grade below the ceiling is allowed (an analyst may be more cautious than the evidence).
A grade above it is `grade-exceeds-evidence`, a high finding: the tool refuses. A claim
that declares no grade at all is `no-grade`, also high — there is no silent default.

## Weights

Each item can carry an Admiralty reliability band (`A`–`F`) and the ACH score weights it
(`A` 1.0 … `E` 0.2, `F` 0.5 for "cannot be judged"). Ranking by weighted inconsistency
means a `C3` report does not move the judgement as much as an `A1` one. Without a band,
every item weighs the same.

## One validator, one severity table

`validate_bundle()` is called by both the factory (`stixforge`) and the gate
(`sharegate`). Structural breakage, a missing marking, an unresolved reference, a
duplicate id or a wrong `spec_version` are high findings; an expired indicator, a bundle
with no marking definition or an unknown marking are medium; a deprecated `TLP:WHITE` is
low. The table is in one place so the two tools can no longer disagree.

It also refuses to walk a bundle over 20,000 objects: `checked: false` and
`stix-too-large`, which the CLIs map to exit code 2. Not checked is not clean.

The TLP markings are the OASIS TLP 2.0 objects, so `TLP:CLEAR` and `TLP:AMBER+STRICT`
exist as first-class labels and `TLP:WHITE` is recognised only to be flagged.

## Traceability pins content

`link()` verifies the id a document cites against the upstream file, and verifies
`<kind>_hash` when the document records one. `external_references()` emits
`<id>@<sha256:12>`, so a STIX report says which exact judgement it came from — an edited
dossier no longer keeps the same identity without notice.

## Limits

`read_text` and `read_json` refuse files over 8 MiB or JSON nested deeper than 64 levels,
with exit code 2. A tool that reads whatever it is handed can be exhausted by a 2 GB
document, and a crash is not a finding.

## Schemas

The six formats are pinned by the schemas in `src/cti_method/schemas/` and shipped with
the package (`cti_method.schema.document("judgement")`). `--strict` on `assessment assess`
and `cryptonym assess` validates the verdict against `judgement.schema.json`; without the
`schemas` extra the command reports that it could not check.

## Install

```console
$ uv sync --all-packages     # in the workspace
$ pip install -e packages/cti-method
$ pip install 'cti-method[schemas]'   # optional: runtime schema validation
```

No runtime dependencies: Python 3.11 or newer and the standard library.

## Licence

MIT. See [LICENSE](https://github.com/Falsifyer/Defensible-CTI/blob/main/LICENSE).
