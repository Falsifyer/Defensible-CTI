# Scope

**This repository is a proof of concept and a portfolio artefact. It is not a production
system.**

It exists to show a way of working: a CTI method whose rules are executable, and a set of
tools that refuse a claim, a grade or a bundle when the evidence does not support it. The
code is tested and reproducible; the claims about the world are not made.

## What it is

- A reference implementation of an analytic method: PIR → graded judgement → ledger →
  hunt plan → STIX product → pre-share gate.
- A set of local command-line tools and a local MCP facade.
- A test bench: 375 tests, a synthetic/illustrative corpus, a published evaluation protocol
  for a future external corpus.
- A blog/portfolio project, run on personal equipment and public or synthetic data.

## What it is not

- **Not production.** No SLA, no on-call, no support contract, no availability guarantee,
  no multi-tenant deployment, no hosted service.
- **Not an attribution engine.** It does not decide who an actor is. It re-derives a
  judgement from the evidence it is given and exposes the result, including abstentions.
- **Not an accuracy claim.** The corpus is illustrative and synthetic. The numbers
  `23 calls / 1 abstention / 1 unsupported` and `Brier 0.0775` are mechanism checks, not
  estimates of real-world precision.
- **Not a data platform.** No ingestion, database, correlation engine or feed service.
- **Not a company product.** No employer data, code, infrastructure, credentials, client
  names or internal reports are used. Nothing here implies endorsement by an employer.
- **Not a network service.** The MCP servers are a local development surface; they are not
  designed to be exposed to the internet.

## Data and sources

- Demo actors (`NIGHTJAR`, `SALTWIND`) are fictional.
- The published dossier uses public sources; the corpus is illustrative.
- Do not put employer data, client data, TLP:AMBER/RED material or personal data in this
  repository.
- If you add a source, record its URL and, where the licence permits, a snapshot hash. Do
  not redistribute paywalled text.

## Security posture

- Local input, local output; no telemetry.
- The ledger is tamper-evident when verified with an anchor (`--head-file`/`--expect-head`).
  A bare `--verify` is documented as unable to see a tail truncation.
- MCP tools read local paths; treat the server as a development surface and do not expose it
  without authentication, path confinement and a threat model.
- `sharegate`'s sensitive-content check is a heuristic guard, not a DLP product.

## Support

Issues are read, not promised. There is no maintenance SLA. If you need production support,
this repository is the wrong artefact; use it as a reference, not as a dependency.

## Licence and attribution

MIT for this code. STIX 2.1 schemas are BSD-3-Clause and are attributed where they are
vendored or linked. Public sources are cited, not copied beyond their terms.

## The sentence to keep

> Reference implementation / proof of concept. No production support. The corpus is
> illustrative; real-world accuracy is not claimed. Opinions are the author's, not an
> employer's.
