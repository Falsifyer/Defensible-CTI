# Data model

Cryptonym's model deliberately keeps four things apart that platforms tend to conflate.

| Concept | Type | Meaning |
|---|---|---|
| Designation | `model.designation.Designation` | One vendor's name. **Not** a claim about identity. |
| Evidence | `model.evidence.Evidence` | A typed item, graded against each hypothesis. |
| Assessment | `model.assessment.Assessment` | The versioned, graded judgement for one pair. |
| Linkage | `reconcile.graph.Linkage` | A graded edge between two designations. |

## Hypotheses

`same_actor` (H1) and `distinct_but_overlapping` (H2) are the default. H3,
`brokered_shared_access`, is opt-in: declare it in the dossier when the evidence suggests a
broker. If it is always present, it ties every case where nothing contradicts it — silence
is not support.

## Evidence types and two senses of "diagnostic"

`infrastructure`, `code`, `operator` are **identity-supporting**; `tactics`,
`linguistic`, `structural`, `open_source` are not. Separately, an item is
**discriminating** (ACH's sense) when it is not consistent with every hypothesis. The
two are different questions and the engine reports both.

## Mapping to STIX 2.1

| Cryptonym | STIX |
|---|---|
| Designation | `x-cryptonym-designation` custom object (carries vendor, name, source) |
| Linkage | `x-cryptonym-linkage` custom object (carries confidence, assessment id, refs) |
| Bundle | `bundle` wrapping the objects, with deterministic identifiers |

A linkage is exported as its own object even at high confidence, so a consumer can always
see *why* two names are linked. A flat `ThreatActor.aliases` list cannot represent that,
which is precisely why Cryptonym does not use one. The output is validated against the
official `stix2` library in CI (`tests/test_stix_conformance.py`).

## Mapping to MISP

A MISP Galaxy cluster is emitted with aliases flagged `assessed_not_asserted`, carrying
the confidence and the assessment id per value and in `meta`.

## Mapping to sources (ingest)

| Source | Adapter | Behaviour |
|---|---|---|
| MISP Galaxy | `ingest.misp_galaxy` | One designation per canonical name and synonym |
| MITRE ATT&CK | `ingest.attack_stix` | One designation per intrusion-set name and alias |
| OpenCTI | `ingest.opencti` | One designation per actor name and alias |
