# cti-suite

**Seven commands, eight packages, one intelligence cycle — and the cycle is in the data, not in
the prose.** Each tool refuses something the cycle should not allow: a requirement with no
decision behind it, a judgement without evidence for it, a grade the evidence cannot support,
a hypothesis that cannot be refuted, a product with no marking, a bundle that may not travel.

> **Status: 0.1, proof of concept / portfolio — not production.** The mechanism is tested
> (300+ tests, CI, one STIX validator, published schemas); real-world accuracy is **not**
> claimed, and the corpus is illustrative — it says so. It reports calls, abstentions and
> unsupported cases separately (currently 23 / 1 / 1); none of those is an accuracy
> claim. There is no support SLA: issues are read, not promised. See [`SCOPE.md`](SCOPE.md).

## Start with the door

The cycle is the argument; the gate is the door. Two commands answer the question every CTI
team gets wrong at least once:

```console
$ git clone https://github.com/Falsifyer/Defensible-CTI && cd Defensible-CTI
$ uv sync --all-packages
$ uv run stixforge build demo/product.json -o /tmp/bundle.json
$ uv run sharegate check /tmp/bundle.json          # exit 1 if it may not travel
$ uv run stixforge validate /tmp/bundle.json          # add --external for the schema validator
```

The rest — requirements, the evidence ceiling, the hunt plan, the ledger — is what makes that
gate mean something. `make demo` runs the whole chain in one command.

| Command | Package | Refuses |
|---|---|---|
| `pir validate` | `packages/pir` | a requirement that does not name the decision it informs |
| `cryptonym assess` | `packages/cryptonym` | a merge that the evidence only supports as overlap |
| `assessment assess` | `packages/assessment` | a declared confidence above what the evidence supports |
| `huntplan validate` | `packages/huntplan` | a hypothesis that cannot be refuted, or a plan with no closure |
| `stixforge build` | `packages/stixforge` | a product that does not say who says it, or when |
| `sharegate check` | `packages/sharegate` | a bundle that claims to travel further than it may |
| `ctisuite report` | `packages/cti-suite` | — it renders the cycle as one artifact |

Two packages are infrastructure, not commands: **`cti-method`** owns the shared core (the
grade ceiling, ACH, the adjudication filter, the single STIX validator, the exit-code
contract, the trace), and **`cti-suite`** owns the readable product and one MCP facade.

## What it is

A **workspace** (uv) with eight installable packages that also run as one chain:

```
requirement → judgement → ledger → hunt plan → STIX product → gate → product
      pir     cryptonym   assessment   huntplan    stixforge   sharegate   cti-suite
```

`make demo` runs the seven steps on fictional data (NIGHTJAR and SALTWIND do not exist).
**Every step after the first reads the file the previous step wrote** and verifies the
identifier it cites against it: a mismatch is a high finding, not a typo. The identifiers
travel into the STIX `report` as `external_references`, so a consumer can walk back from the
bundle to the assessment and to the requirement.

Every package keeps its own name, its own command, its own version and its own `CHANGELOG`.

## What it is not

- **Not a platform.** No web UI, no ingestion, no database, no correlation engine. Each
  command reads a file and writes a file.
- **Not one product with six modes.** The packages do not share a runtime dependency except
  through `cti-method`, which is a real path dependency inside the workspace.
- **Not a substitute for judgement.** Every tool checks that a decision is stated and
  defensible; none of them decides whether the analysis is right.

## Install

```console
$ uv sync --all-packages --all-extras   # or: make install
```

That creates one virtual environment with the eight packages in editable mode. The OpenCTI
adapter consumes an already-parsed actor document; it does not depend on `pycti`.

## Use

```console
$ make demo                     # the whole cycle, fictional data, outputs in demo/out/
$ ctisuite chain --dir demo     # the same chain, in code, with one exit code
$ make test                     # every test suite, one process
$ make lint types eval security # ruff, mypy, the evaluation baselines, pip-audit
$ uv run stixforge build demo/product.json -o /tmp/bundle.json --assessment demo/assessment.json
$ uv run sharegate check /tmp/bundle.json
```

The input formats are pinned by the schemas shipped in
[`cti-method`](packages/cti-method/src/cti_method/schemas): a consumer can check a document
before using it, `schema_version` is part of every format, and `--strict` validates a
judgement against its published schema.

## Method

Six conventions run through the suite, and each one is enforced somewhere you can point at:

1. **Exit codes are the contract.** `0` clean, `1` a high finding, `2` it could not check.
   *Not checked is not clean*: an unreadable file is `2`, never `1`. One implementation in
   `cti_method.contract`, and one test that runs all six entry points against a missing file.
2. **The tool refuses; it does not warn.** A requirement with no decision, a plan with no
   closure, a bundle with no marking or a declared grade above the ceiling fail the run.
3. **The evidence caps the grade.** `high` needs at least one diagnostic item that
   discriminates **and** two independent sources; shared tradecraft alone cannot exceed
   `low`. Independence is structural: a dossier registers its sources and says which
   derived from which, so two reports from one publisher are one voice. Evidence that
   contradicts the favoured hypothesis lowers the ceiling. A claim that declares no grade is
   refused, not defaulted, and a declared grade above the ceiling is refused too.
4. **One STIX validator, one severity table.** The factory and the gate call
   `cti_method.stix.validate_bundle`; a test asserts both report identical findings.
5. **TLP 2.0, not an alias.** The markings are the OASIS TLP 2.0 objects, so `TLP:CLEAR` and
   `TLP:AMBER+STRICT` are first-class and `TLP:WHITE` is recognised only to be flagged.
6. **The trace pins content, not just an id.** `<id>@<sha256>` travels in the STIX
   `external_references`, so an edited dossier no longer keeps the same identity silently.
7. **Not checked is not clean, including size.** Input over 8 MiB, JSON nested beyond 64
   levels or a bundle over 20,000 objects is refused with exit code 2, not walked until it
   dies.
8. **One version per package.** Tags are `cryptonym-v0.7.0`, `stixforge-v0.2.0`, and so on:
   eight versions that mean something, not one number for everything.

## One MCP surface

`ctisuite-mcp` is the supported server: prefixed tools for the six steps plus
`suite_report`. Each package also ships its own `*-mcp` server as a **development**
surface for working on that step in isolation; do not register all seven with one client.

## Licence

MIT. See [`LICENSE`](LICENSE).

---

**Martín Eliseo** — cyber threat intelligence.
[GitHub](https://github.com/Falsifyer) · [falsifyer.github.io](https://falsifyer.github.io)
