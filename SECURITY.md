# Security

## Reporting

Open a private advisory at <https://github.com/ME0094/cti-suite/security/advisories/new>.
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
- A ledger entry that can be edited without `assessment ledger --verify` noticing.
- Input that exhausts memory, or a path the user passes by mistake.

## Out of scope

That a well-formed product says something wrong is not a vulnerability: the tools check
shape, marking, traceability and the consistency between a claim and its evidence — not the
analyst's judgement.
