# cti-suite

**Six tools for one intelligence cycle, in one repository.** Each one refuses something the cycle
should not allow: a requirement with no decision behind it, a judgement without evidence for it, a
product with no marking, a bundle that may not travel, a hypothesis that cannot be refuted.

| Command | Package | Refuses |
|---|---|---|
| `pir validate` | `packages/pir` | a requirement that does not name the decision it informs |
| `cryptonym assess` | `packages/cryptonym` | a merge that the evidence only supports as overlap |
| `assessment assess` | `packages/assessment` | a claim graded on one axis when it needs two |
| `huntplan validate` | `packages/huntplan` | a hypothesis that cannot be refuted |
| `stixforge build` | `packages/stixforge` | a product that does not say who says it |
| `sharegate check` | `packages/sharegate` | a bundle that claims to travel further than it may |

## What it is

A **workspace** (uv) with six installable packages that also run as one chain:

```
requirement → judgement → ledger → hunt plan → STIX product → gate
      pir     cryptonym   assessment   huntplan    stixforge   sharegate
```

`make demo` runs the six in order on fictional data (NIGHTJAR and SALTWIND do not exist), each
consuming what the previous one produced. Every package keeps its own name, its own command, its own
version and its own `CHANGELOG`.

## What it is not

- **Not a platform.** No web UI, no ingestion, no database, no correlation engine. Each command reads
  a file and writes a file.
- **Not one product with six modes.** The packages do not share a runtime dependency, except
  `assessment`, which imports the graded core from `cryptonym` — inside the workspace, as a real
  path dependency, with no token and no `git+https` install.
- **Not a substitute for judgement.** Every tool checks that a decision is stated and defensible; none
  of them decides whether the analysis is right.

## Install

```console
$ uv sync --all-packages --all-extras   # or: make install
```

That creates one virtual environment with the six packages in editable mode. With plain pip:

```console
$ pip install -e packages/cryptonym -e packages/assessment -e packages/sharegate \
              -e packages/stixforge -e packages/pir -e packages/huntplan
```

## Use

```console
$ make demo                     # the whole cycle, fictional data, outputs in demo/out/
$ make test                     # the six test suites
$ uv run stixforge build demo/product.json -o /tmp/bundle.json
$ uv run sharegate check /tmp/bundle.json
```

Each package keeps its own README with its full usage: [cryptonym](packages/cryptonym/README.md),
[assessment](packages/assessment/README.md), [sharegate](packages/sharegate/README.md),
[stixforge](packages/stixforge/README.md), [pir](packages/pir/README.md),
[huntplan](packages/huntplan/README.md).

## Method

Three conventions run through the six:

1. **Exit codes are the contract.** `0` clean, `1` a high finding, `2` it could not check. *Not
   checked is not clean*, and no tool returns 0 when it could not look.
2. **The tool refuses; it does not warn.** A requirement with no decision, an ungraded indicator, a
   bundle with no marking or a hypothesis that cannot be refuted fail the run by design.
3. **One version per package.** Tags are `cryptonym-v0.6.0`, `stixforge-v0.1.0`, and so on: six
   versions that mean something, not one number for everything.

## Licence

MIT. See [`LICENSE`](LICENSE).

---

**Martín Eliseo** — cyber threat intelligence.
[GitHub](https://github.com/ME0094) · [me0094.github.io](https://me0094.github.io)
