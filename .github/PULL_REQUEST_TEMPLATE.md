## What this changes

<!-- One paragraph. Which step of the cycle, and what it now refuses. -->

## Contracts touched

<!-- Tick what applies. A contract change needs a schema_version bump and a CHANGELOG entry. -->

- [ ] findings or severities
- [ ] exit codes
- [ ] input format (`schemas/*.schema.json`)
- [ ] TLP handling
- [ ] none

## How it was verified

```console
$ uv run pytest -q
$ uv run ruff check packages
$ uv run mypy
$ make demo
```

<!-- Paste the result. "Tests pass" without the output is not verification. -->

## Evaluation baseline

<!-- If the method changed: which expected.json was regenerated, and why. -->
