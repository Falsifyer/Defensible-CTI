# Architecture

Cryptonym is a pipeline, not a monolith. The core is standard-library Python; every
external system is an adapter behind an optional dependency.

```
ingest → normalize → evidence catalogue → assess (ACH + 2 axes) → reconcile (graph) → publish → score
```

| Stage | Package | Status (v0.1.0) |
|---|---|---|
| Ingest designations from MISP Galaxy / ATT&CK / OpenCTI | `cryptonym.ingest` | implemented (offline, dict-based) |
| Normalize into the model | `cryptonym.model` | implemented |
| Assess (consistency matrix, least-inconsistent hypothesis) | `cryptonym.assess` | implemented |
| Reconcile (graded edges, threshold clusters) | `cryptonym.reconcile` | implemented |
| Publish (markdown / STIX / MISP / TAXII) | `cryptonym.export` | implemented |
| Capture sources (bytes + hash) | `cryptonym.snapshot` | implemented |
| Fetch sources over the network (validated) | `cryptonym.ingest.fetch` | implemented |
| Score per split (false-merge rate, calibration) | `cryptonym.evaluate` | implemented |
| Adjudicate external truth (filter, coverage) | `cryptonym.evaluate.adjudication` | implemented |

## Design choices that are load-bearing

- **Nothing merges.** `reconcile.graph` computes clusters; it never deletes nodes or
  edges. This is the whole difference from a platform alias list.
- **Ingest keeps names apart.** A source that stores aliases as one flat list is mapped
  into *separate* designations, so whether they are the same actor becomes a graded
  linkage rather than a given.
- **Optional dependencies stay optional.** `networkx` and the service SDKs are imported
  lazily; the core installs and the CI runs with no third-party runtime dependency.
  STIX is emitted as JSON directly, then validated against the official `stix2` library
  in a conformance test.
- **Fail closed at the boundary.** Untrusted dossiers, source URLs and fetched payloads
  go through `cryptonym.security` before use; network access lives only in
  `ingest.fetch`/`snapshot` and is delegated to an injected fetcher so the core stays
  offline and testable.
- **What was read is captured.** `cryptonym.snapshot` records a source's bytes and
  SHA-256, so a judgement can be re-derived against the exact document it was built from.
- **The method is the product.** The engine re-derives the published judgement from the
  published evidence, and CI fails if the two drift (`evaluation/run_evaluation.py`).

## What is deliberately absent

A UI, a live TAXII server, and network source fetching. Ingest consumes already-fetched
documents; the caller fetches. Each is a deployment concern, not a method concern.
