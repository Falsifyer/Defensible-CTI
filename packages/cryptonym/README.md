# Cryptonym

**Actor alias reconciliation with provenance, two-axis confidence and falsifiable merges.**

> A merge is a hypothesis, not a fact.

Vendor designations for the same adversary drift — *Volt Typhoon*, *VOLTZITE*, *Insidious
Taurus*, *BRONZE SILHOUETTE*, *UNC3236* — and platforms such as MISP, OpenCTI and ATT&CK
store those names as a **flat list of assertions**. Cryptonym treats every linkage between two
designations as a **graded, evidenced, reversible hypothesis** instead: it never collapses
nodes, it separates diagnostic evidence from non-diagnostic overlap, and it carries the
method — not just the result.

**Status: v0.7.0.** Ingest (MISP Galaxy / ATT&CK / OpenCTI), the ACH engine, graded
reconciliation, STIX 2.1 / MISP Galaxy / TAXII export, the markdown product, source
snapshots and a **per-split evaluation harness** over an adjudicated corpus. The graded core
now lives in [`cti-method`](../cti-method/README.md), which this package consumes rather
than owns. See [method](src/cryptonym/docs/method.md) and
[adjudication](src/cryptonym/docs/adjudication.md).

## Why this exists

Cryptonym answers a standing question:

> *When vendor designations diverge, how much confidence does the evidence support for
> treating them as the same actor — and what would break the tie?*

A naming judgement changes decisions. An incident responder, a hunting team or a
procurement choice should not treat two designations as one actor without a stated
confidence — and should be able to see the evidence that would separate them.

## The method (the differentiator)

Cryptonym is a *method made executable*, not another CTI platform. The stack
(OpenCTI + MISP + STIX2/TAXII) is the plumbing; none of it does this:

- **Merges are reversible.** Designations are nodes; a linkage is a graded edge with
  provenance. A cluster is *computed at a threshold*, never a deleted fact.
- **Diagnostic vs non-diagnostic evidence.** Shared tradecraft cannot sustain a merge on its
  own; only infrastructure, code or operator artefacts can.
- **ACH, mechanised.** Evidence is tested against all competing hypotheses at once; the
  favoured hypothesis is the one with the *least inconsistent* evidence, not the loudest.
- **The evidence caps the grade.** `high` needs a diagnostic discriminating item **and** two
  independent sources; shared tradecraft alone cannot exceed `low`. Independence is
  structural: the dossier registers its sources (`id`, `publisher`, `derived_from`,
  `reliability`), so two reports from one vendor are one voice and a derived source does not
  count twice. Evidence that contradicts the favoured hypothesis lowers the ceiling, and
  items are weighted by their Admiralty band. A dossier that claims more than that is
  refused (`grade-exceeds-evidence`); one that declares no grade is refused too.
- **Two axes, per claim.** *Confidence* (sourcing/reasoning) is kept separate from
  *probability* (likelihood of the outcome).
- **Chains expose their weakest link.** Confidence does not multiply cleanly along a chain
  of `same-as` assertions, so Cryptonym never averages it away.
- **The method is scored.** A golden-pair harness reports the **false-merge rate** (the
  costly error) and checks that the **derived** ceiling calibrates — reported **per split**,
  so the held-out result is never hidden behind the development one. The harness also says
  how many cases declare more than their evidence supports.
- **Truth is external.** The accuracy figures come only from an **adjudicated corpus**: a
  binary truth must be asserted by independent sources, a disagreement is recorded as
  *contested*, and `--strict` rejects any ungrounded claim.
- **Sources are snapshotted.** What a judgement was built from is captured with its
  SHA-256, so an assessment can be re-derived against the exact bytes it saw.

## What it is not

- **Not a verdict.** No attribution, no ground truth, no private telemetry.
- **Not a platform.** It feeds OpenCTI/MISP/STIX; it does not replace them.
- **Not a de-duplicator.** It does not silently collapse two names into one.

## Install

```bash
pip install -e ../cti-method -e .            # core + this package
pip install -e ../cti-method -e '.[cti]'     # optional: stix2 conformance, graph analytics
pip install -e ../cti-method -e '.[misp]'    # optional: MISP Galaxy adapter
pip install -e ../cti-method -e '.[dev]'     # tests, lint, security scan
```

The optional integrations are extras in `pyproject.toml`; the `requirements-*.txt` files
that duplicated them have been removed.

## Use

```bash
# Capture a source (record its bytes and hash), or re-check a recorded one:
cryptonym snapshot --source https://example.org/advisory.json --output advisory.snapshot.json
cryptonym snapshot --verify advisory.snapshot.json

# Normalise names from a source into separate designations (local file or URL):
cryptonym ingest --source misp-galaxy --input galaxy.json
cryptonym ingest --source attack-stix --url https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/enterprise-attack/enterprise-attack.json

# Re-derive and print the machine-readable judgement (exit 1 if the grade exceeds the ceiling):
cryptonym assess assessments/voltzite-vs-volt-typhoon/assessment.json

# The human product, and shareable forms:
cryptonym render  assessments/voltzite-vs-volt-typhoon/assessment.json
cryptonym export  assessments/voltzite-vs-volt-typhoon/assessment.json --format stix
cryptonym export  assessments/voltzite-vs-volt-typhoon/assessment.json --format misp
cryptonym export  assessments/voltzite-vs-volt-typhoon/assessment.json --format taxii

# Score the method per split, reproducibly:
python evaluation/run_evaluation.py --corpus --check

# Score the adjudicated corpus; fail if an ungrounded truth crept in:
python evaluation/run_evaluation.py --adjudicated --check --strict
```

## Structure

```
src/cryptonym/
  model/        designations, evidence, two-axis grading, assessment
  assess/       the ACH engine (consistency matrix, least-inconsistent hypothesis)
  reconcile/    the graded graph (clusters at threshold, weakest link)
  ingest/       MISP Galaxy / ATT&CK / OpenCTI adapters + safe network fetch
  export/       markdown product + STIX 2.1 / MISP Galaxy / TAXII
  evaluate/     corpus scoring on top of cti_method's confusion and calibration
  snapshot.py   capture a source's bytes and hash for reproducibility
  security.py   input and endpoint validation
  docs/         method, adjudication, architecture, data model, evaluation
assessments/    versioned adjudications (one dossier per pair)
data/           curated designations and evidence catalogues
evaluation/     golden-pair corpus (development + held-out) + adjudicated corpus, baselines, CI harness
```

## Contributing & license

See [CONTRIBUTING](https://github.com/Falsifyer/Defensible-CTI/blob/main/CONTRIBUTING.md) and [SECURITY](https://github.com/Falsifyer/Defensible-CTI/blob/main/SECURITY.md). MIT — see
[LICENSE](https://github.com/Falsifyer/Defensible-CTI/blob/main/LICENSE).

## Use as an MCP server

```bash
pip install -e '.[mcp]'
cryptonym-mcp          # stdio transport; register in your MCP client
```

See [docs/mcp.md](src/cryptonym/docs/mcp.md). The suite also ships one facade
(`ctisuite-mcp`) that exposes every tool under a prefixed name.

## The shared core

Every tool in the family imports one package — the graded core — instead of
reimplementing it:

```python
from cti_method import Assessment, Confidence, Judgement, filter_adjudication
```

`cryptonym.method` still exports the same names for existing consumers. See
[method-api](src/cryptonym/docs/method-api.md).

## Demo end-to-end

The cycle runs from the repository root: `make demo` executes the seven steps over a
fictional case (NIGHTJAR and SALTWIND do not exist) and each step consumes what the previous
one produced. See the [suite README](https://github.com/Falsifyer/Defensible-CTI/blob/main/README.md#use).

---

**Martín Eliseo** — cyber threat intelligence.
[GitHub](https://github.com/Falsifyer) · [falsifyer.github.io](https://falsifyer.github.io)
