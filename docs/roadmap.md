# Roadmap and accepted gaps

What is implemented is in the READMEs and the CHANGELOGs. This file is the honest list of
what is **not** done, why, and what would close it.

## Needs an action outside the repository

| Gap | Why it is not done here | What closes it |
|---|---|---|
| **PyPI publication** | needs a PyPI account: pending publishers are web-UI only and do not reserve a name until the first upload | environment `pypi` created and workflow ready; follow [`publishing.md`](publishing.md) |
| **The release workflow has never run against a real tag** | running it means creating a public tag | `workflow_dispatch` with `dry_run: true` (the default) and then a first real tag |
| **`ME0094/huntplan` stays public and obsolete** | it is a separate repository, kept for a while on purpose | apply the banner in [`deprecation-huntplan.md`](deprecation-huntplan.md), freeze the code, stop syncing it |
| **Artefact signing** | configured in the release workflow, never executed | the first release; verify with `cosign verify-blob` |

## Method gaps

| Gap | State | What would close it |
|---|---|---|
| **External corpus** | the corpus is illustrative; the `heldout-*` cases are synthetic and exist to exercise the ceiling | a corpus adjudicated by someone other than the author, with real disagreements |
| **Probability calibration at scale** | the Brier score is computed, but on 22 illustrative cases (`0.0853`) and 2 admissible ones (`0.04`) | the external corpus above, with estimative claims |
| **Source independence** | structural (registry + `derived_from`), but still declared by the author | ingest the source graph from the CTI platform instead of the dossier |
| **Contradiction rule** | one step down when contradiction outweighs support; weights are a hand-set table | calibrate the step and the weights against outcomes |
| **ACH weights** | Admiralty band → weight is a fixed table | derive it from the evaluation once there is an external corpus |

## Engineering gaps

| Gap | State | What would close it |
|---|---|---|
| **Fuzzing** | property tests for the ceiling; no fuzzing of the JSON/STIX parsers | `atheris`/`hypothesis` campaigns over `validate_bundle` and `read_json` |
| **Coverage floor** | 89% measured, not enforced | `--cov --cov-fail-under=85` once the CLI paths are covered |
| **Multi-platform CI** | Linux only; `demo/run.sh` is POSIX shell | a Windows job for the Python paths (the shell wrapper is not used there) |
| **Six development MCP servers** | kept for working on one step in isolation, documented as development surface | remove them if the facade is enough |
| **`sharegate` policy engine** | applies TLP/STIX rules; no per-organisation policy | out of scope by design |

## Documentation gaps

- `packages/cryptonym/src/cryptonym/docs/mcp.md` describes the per-package server; it should
  say it is a development surface.
- The `huntplan` worked cases were written before the ATT&CK v18 migration; their telemetry
  wording predates Data Components. They are still correct as cases, not as vocabulary.
- No translations. The internal notes are Spanish and the published text is English; that
  is a convention, not an accident.
