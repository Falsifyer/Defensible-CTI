# Security

## Reporting

Open a private advisory at <https://github.com/ME0094/cti-suite/security/advisories/new>. Please do
not open a public issue for an unfixed flaw.

## Scope

The six packages read JSON or text files and write to standard output or to a file the user names.
None of them calls the network on the default path, and none executes anything from its input. What
matters:

- **A false permit** from `sharegate`: a bundle reported as shareable that should not leave, or with
  a marking weaker than it carries. That is the failure the tool exists to prevent.
- A bundle from `stixforge` that claims a marking it does not carry, or identifiers that collide and
  silently merge two objects.
- `assessment` or `cryptonym` grading a claim as strong when the evidence does not support it.
- Input that exhausts memory, or a path the user passes by mistake.

## Out of scope

That a well-formed product says something wrong is not a vulnerability: the tools check shape,
marking and traceability, not the analyst's judgement.
