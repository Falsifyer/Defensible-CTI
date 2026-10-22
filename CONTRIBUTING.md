# Contributing

The suite is small on purpose. The rules below are the same ones the tools enforce on
other people's documents.

## What belongs here

A change belongs in this repository if it makes one of the six steps **refuse something
the intelligence cycle should not allow**, or if it makes that refusal cheaper to verify.
A feature that makes a tool agree with whatever it is given is not a feature.

## Before you open a pull request

```console
$ uv sync --all-packages --all-extras
$ uv run pytest -q          # all packages, one process
$ uv run ruff check packages
$ uv run mypy
$ make demo                 # the chain, end to end
```

The evaluation harness is part of CI: if you change the method, the committed baselines in
`packages/cryptonym/evaluation/*/expected.json` must be regenerated **and** the diff
explained in the pull request. Regenerating a baseline to make CI green without saying why
is the failure mode the baseline exists to catch.

## Adding a package

1. Create `packages/<name>/` with `pyproject.toml`, `README.md`, `CHANGELOG.md` and `src/<module>/`.
2. Depend on `cti-method`; do not reimplement findings, exit codes or the STIX validator.
3. Declare it in the root `pyproject.toml` (`[tool.uv.sources]` and the `dev` group) and in
   the CI matrix if it has its own tests.
4. Add it to `packages/cti-suite/tests/test_versions.py` and to the release workflow's tag
   mapping.
5. Tag it `<name>-v<version>`, never a single suite-wide tag.

## Versioning

One version per package, one tag per package (`cryptonym-v0.7.0`, `stixforge-v0.2.0`). A
breaking change to an input format bumps `schema_version` in `schemas/` in the same commit.

## Language

Code, comments, docstrings and the internal notes are in Spanish; everything published —
README, `docs/`, CHANGELOG, release notes, issue and pull request text — is in English.
Identifiers, file names and CLI output are English.

## Commit messages

Spanish, imperative, one idea per commit. If the commit changes a contract (exit codes,
findings, schemas, TLP handling), say so in the body.

## Security

Do not open a public issue for a vulnerability. See [`SECURITY.md`](SECURITY.md).
