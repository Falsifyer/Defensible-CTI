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

`pip-audit` and `pip check` run in CI. No advisory is ignored. The `pycti` extra was
removed because the OpenCTI adapter consumes an already-parsed actor document and never
imports `pycti`; the workspace no longer overrides `setuptools` or `opentelemetry`.

## Out of scope

That a well-formed product says something wrong is not a vulnerability: the tools check
shape, marking, traceability and the consistency between a claim and its evidence — not the
analyst's judgement.
