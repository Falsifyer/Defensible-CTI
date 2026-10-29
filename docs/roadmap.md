# Roadmap and accepted gaps

What is implemented is in the READMEs and the CHANGELOGs. This file is the honest list of
what is **not** done, why, and what would close it.

## Needs an action outside the repository

| Gap | Why it is not done here | What closes it |
|---|---|---|
| ~~**PyPI publication**~~ | **Out of scope since 2026-10-26**: this repository is a test bench, and publishing eight names to PyPI would turn a bench into a product to maintain. `publish.yml` stays as a manual tool, exercised in `dry_run` mode; no name is reserved. | nothing: it is a decision, not a gap |
| ~~**The release workflow has never run against a real tag**~~ | **Closed on 2026-10-26**: eight tags produced eight releases, each with wheel, sdist, CycloneDX SBOM and a sigstore bundle | — |
| ~~**`Falsifyer/huntplan` stays public and obsolete**~~ | **Closed on 2026-10-27**: the banner points at `packages/huntplan` in this suite and the repository is archived (read-only). Nothing pushes to it. | — |
| ~~**Artefact signing**~~ | **Closed on 2026-10-26**: every release carries `<file>.sigstore.json` for the wheel and the sdist, produced keyless through the runner's OIDC token | verify with `sigstore verify identity --bundle <file>.sigstore.json <file>` |

## Method gaps

| Gap | State | What would close it |
|---|---|---|
| **External corpus** | the corpus is illustrative; the `heldout-*` cases are synthetic and exist to exercise the ceiling | a corpus adjudicated by someone other than the author, with real disagreements |
| **Probability calibration at scale** | the Brier score is computed, but on 23 scored of 24 illustrative cases (`0.0775`; 1 abstains, 1 unsupported) and 2 admissible ones (`0.04`) | the external corpus above, with estimative claims |
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
