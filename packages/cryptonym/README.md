# Cryptonym

**Actor alias reconciliation with provenance, two-axis confidence and falsifiable merges.**

> A merge is a hypothesis, not a fact.

Vendor designations for the same adversary drift — *Volt Typhoon*, *VOLTZITE*, *Insidious
Taurus*, *BRONZE SILHOUETTE*, *UNC3236* — and platforms such as MISP, OpenCTI and ATT&CK
store those names as a **flat list of assertions**. Cryptonym treats every linkage between two
designations as a **graded, evidenced, reversible hypothesis** instead: it never collapses
nodes, it separates diagnostic evidence from non-diagnostic overlap, and it carries the
method — not just the result.

**Status: v0.3.0.** Ingest (MISP Galaxy / ATT&CK / OpenCTI), the ACH engine, graded
reconciliation, STIX 2.1 / MISP Galaxy / TAXII export, the markdown product, source
snapshots, a per-split evaluation harness and an **adjudicated corpus with an
external-truth filter** are implemented and tested. See [docs/method.md](docs/method.md)
and [docs/adjudication.md](docs/adjudication.md).

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
- **Diagnostic vs non-diagnostic evidence.** Shared tradecraft cannot sustain a merge on
  its own; only infrastructure, code or operator artefacts can.
- **ACH, mechanised.** Evidence is tested against all competing hypotheses at once; the
  favoured hypothesis is the one with the *least inconsistent* evidence, not the loudest.
- **Two axes, per claim.** *Confidence* (sourcing/reasoning) is kept separate from
  *probability* (likelihood of the outcome).
- **Chains expose their weakest link.** Confidence does not multiply cleanly along a chain
  of `same-as` assertions, so Cryptonym never averages it away.
- **The method is scored.** A golden-pair harness reports the **false-merge rate** (the
  costly error) and checks that confidence grades calibrate — reported **per split**, so
  the held-out result is never hidden behind the development one.
- **Truth is external.** The accuracy figures come only from an **adjudicated corpus**:
  a binary truth must be asserted by independent sources, a disagreement is recorded as
  *contested*, and `--strict` rejects any ungrounded claim.
- **Sources are snapshotted.** What a judgement was built from is captured with its
  SHA-256, so an assessment can be re-derived against the exact bytes it saw.

## What it is not

- **Not a verdict.** No attribution, no ground truth, no private telemetry.
- **Not a platform.** It feeds OpenCTI/MISP/STIX; it does not replace them.
- **Not a de-duplicator.** It does not silently collapse two names into one.

## Install

```bash
pip install -e .                          # core: standard library only
pip install -r requirements-dev.txt       # tests, lint, security scan, STIX conformance
pip install -r requirements-cti.txt       # optional: graph analytics
```

## Use

```bash
# Capture a source (record its bytes and hash), or re-check a recorded one:
cryptonym snapshot --source https://example.org/advisory.json --output advisory.snapshot.json
cryptonym snapshot --verify advisory.snapshot.json

# Normalise names from a source into separate designations (local file or URL):
cryptonym ingest --source misp-galaxy --input galaxy.json
cryptonym ingest --source attack-stix --url https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/enterprise-attack/enterprise-attack.json

# Re-derive and print the machine-readable judgement:
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
  evaluate/     confusion, false-merge rate, calibration, per-split scoring, adjudication filter
  snapshot.py   capture a source's bytes and hash for reproducibility
  security.py   input and endpoint validation
assessments/    versioned adjudications (one dossier per pair)
data/          curated designations and evidence catalogues
evaluation/    golden-pair corpus (development + held-out) + adjudicated corpus, baselines, CI harness
docs/          method, adjudication, architecture, data model, evaluation
```

## Contributing & license

See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md). MIT — see [LICENSE](LICENSE).

## Use as an MCP server

```bash
pip install -e '.[mcp]'
cryptonym-mcp          # stdio transport; register in your MCP client
```

See [docs/mcp.md](docs/mcp.md).

## The shared core

Every Cryptonym-family tool imports one piece — the graded-assessment core — instead of
reimplementing it:

```python
from cryptonym.method import Assessment, Confidence, Judgement, filter_adjudication
```

See [docs/method-api.md](docs/method-api.md).

## Demo end-to-end

`demo/` ejecuta la cadena completa sobre un caso **ficticio** (NIGHTJAR y SALTWIND no
existen): dossier -> juicio -> bundle STIX -> puerta de cumplimiento -> ledger graduado.

```console
$ make -C demo install   # instala esta y las dos hermanas en .venv-demo
$ make -C demo demo
```

Lo que demuestra no es el caso, es la cadena: cada paso consume la salida del anterior y
ninguno acepta lo que el anterior afirma sin comprobarlo. Y dos cosas que se ven al correrla:
el exportador aún marca `TLP:WHITE` (TLP 2.0 lo renombró a `TLP:CLEAR`) y la puerta lo señala;
y el grado no se declara, sale de la evidencia.

---

**Martín Eliseo** — cyber threat intelligence.
[GitHub](https://github.com/ME0094) · [me0094.github.io](https://me0094.github.io)
