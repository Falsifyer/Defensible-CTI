# Publishing to PyPI

> **Not part of the current scope.** Since 2026-10-26 this repository is a test bench and PyPI is out of
> scope: nothing is published and no name is reserved. This file stays as the runbook for the day that
> changes, and `publish.yml` stays because its `dry_run` mode is a useful build check.

The repository side is done: the `pypi` environment exists, restricted to `main`, and
`.github/workflows/publish.yml` publishes one package per run with OIDC. What is left needs
a PyPI account, because PyPI has **no API** for this part: pending publishers are created in
the web UI, and a pending publisher does **not** reserve the name until the first upload.

## One-time setup (needs the PyPI account holder)

1. Sign in at <https://pypi.org> with 2FA enabled.
2. Go to **Account settings → Publishing** (<https://pypi.org/manage/account/publishing/>).
3. Add a **pending publisher** for each package, with exactly these values:

| PyPI project | Owner | Repository | Workflow | Environment |
|---|---|---|---|---|
| `cti-method` | `ME0094` | `cti-suite` | `publish.yml` | `pypi` |
| `cryptonym` | `ME0094` | `cti-suite` | `publish.yml` | `pypi` |
| `assessment-mcp` | `ME0094` | `cti-suite` | `publish.yml` | `pypi` |
| `sharegate` | `ME0094` | `cti-suite` | `publish.yml` | `pypi` |
| `stix-forge` | `ME0094` | `cti-suite` | `publish.yml` | `pypi` |
| `pir-ledger` | `ME0094` | `cti-suite` | `publish.yml` | `pypi` |
| `huntplan` | `ME0094` | `cti-suite` | `publish.yml` | `pypi` |
| `cti-suite` | `ME0094` | `cti-suite` | `publish.yml` | `pypi` |

The workflow field is the **file name**, not the path. All eight names were free on PyPI when
this was written (checked against `https://pypi.org/pypi/<name>/json`); a pending publisher
can be invalidated if someone else registers the name first, so publish soon after creating
them.

## Publish

One manual dispatch per package, from `main`, with `dry_run` unchecked:

```console
$ gh workflow run publish.yml -f package=cti-method -f dry_run=false
$ gh run watch
```

Order matters for consumers, not for the registry: publish `cti-method` first (the others
depend on it on PyPI), then the rest, and `cti-suite` last.

```console
$ for package in cti-method cryptonym assessment-mcp sharegate stix-forge pir-ledger huntplan cti-suite; do
    gh workflow run publish.yml -f package="$package" -f dry_run=false
    gh run watch --exit-status
  done
```

## Verify

```console
$ curl -s https://pypi.org/pypi/cti-method/json | jq -r '.info.version'
$ python -m venv /tmp/pypi-check && /tmp/pypi-check/bin/pip install cti-method cti-suite
$ /tmp/pypi-check/bin/ctisuite --version
```

After the first upload the pending publisher becomes a normal publisher; no further
configuration is needed and no token exists anywhere in the repository.

## Why not a token

An API token in a repository secret also works, but it is a long-lived credential that can be
stolen and has to be rotated. OIDC issues a short-lived token per run and binds it to this
repository, this workflow and the `pypi` environment.

## If a name changes

`pyproject.toml` names are the distribution names and cannot be renamed without breaking
imports for consumers. If a name is taken before the first upload, stop and decide: rename
the distribution (and the entry points), or keep the package unpublished.
