# Security

## Reporting

Open a private advisory at <https://github.com/Falsifyer/Defensible-CTI/security/advisories/new>.
Please do not open a public issue for an unfixed flaw.

## Scope

The eight packages read JSON or text files and write to standard output or to a file the
user names. None of them calls the network on the default path (`cryptonym snapshot` and
`ingest --url` are the explicit exceptions, and they validate the endpoint), and none
executes anything from its input. What matters:

- **A false permit** from `sharegate`: a bundle reported as shareable that should not
  leave, or with a marking weaker than it carries. That is the failure the tool exists to
  prevent.
- **A grade above the evidence** that the suite reports as supported: the ceiling in
  `cti_method.grading` is the rule that makes the two-axis grade mean something, and a way
  around it is a vulnerability in the method, not a feature.
- A bundle from `stixforge` that claims a marking it does not carry, identifiers that
  collide and silently merge two objects, or a trace that points at an assessment it did
  not come from.
- A ledger entry that can be edited, or a tail truncated, without `assessment ledger
  --verify` noticing. An anchored `--head-file`/`--expect-head` run is the check that closes
  the tail; a bare `--verify` is documented as not seeing it.
- Input that exhausts memory, or a path the user passes by mistake.

## Dependency advisories

`pip-audit` and `pip check` run in CI. One advisory is accepted and documented:
`PYSEC-2026-3447` (setuptools 82.0.1, fixed in 83). The `opencti` extra pins pycti, which
pins setuptools to a band that excludes 83; setuptools is a build backend and is never
imported by the suite. The default sync therefore excludes the `opencti` extra
(`--no-extra opencti`), which keeps `pip check` clean; enabling it intentionally reintroduces
the unsupported pycti pin combination. If pycti lifts its pin, the ignore is removed in the
same commit.

## Out of scope

That a well-formed product says something wrong is not a vulnerability: the tools check
shape, marking, traceability and the consistency between a claim and its evidence — not the
analyst's judgement.
