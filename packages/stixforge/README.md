# stix-forge

**A bundle is not shareable until it says how far it may travel — and where it came from.**

`stixforge build` turns an intelligence product into a STIX 2.1 bundle with the TLP marking,
the author's identity, the observables, the indicators and a `report` that references all of
them. `stixforge validate` checks the result with the suite's single validator, and with
`--external` hands it to the OASIS tooling.

The bundle is **byte-reproducible**: identifiers are derived from content and `created` is
required, so rebuilding the same product produces the same bytes.

## What it is

- **A producer.** Product JSON in, STIX 2.1 bundle out: marking-definition, identity, SCOs,
  indicators, malware objects and a report with `object_refs`, all with `created_by_ref`
  where it applies.
- **A validator.** The structural checks live in [`cti-method`](../cti-method/README.md) and
  are the ones `sharegate` applies, plus the optional OASIS tooling with `--external`.
- **A traced producer.** `--requirement`, `--assessment` and `--hunt` verify the identifiers
  the product cites and emit them as `external_references` on the report, so a consumer can
  walk back from the bundle to the evidence and the requirement.
- **The other half of `sharegate`.** `sharegate` decides whether a bundle may leave; this is
  the factory that builds one worth gating.

## What it is not

- **Not another OpenCTI.** No web UI, no ingestion, no correlation, no database.
- **No TAXII yet.** TAXII 2.1 publication is deliberately out of scope for 0.2.0; the bundle
  is the unit.
- **It does not judge the analysis.** It checks that the product says who says it, what it
  claims, when, and how far it travels — not whether the claim is true.

## Install

```console
$ pip install -e ../cti-method -e '.[dev]'          # development and tests
$ pip install -e '../cti-method' -e '.[dev,external]' # plus stix2 and stix2-validator
```

## Use

```console
$ stixforge build examples/product.json -o bundle.json
$ stixforge build product.json -o bundle.json \
    --requirement pir.json --assessment assessment.json --hunt hunt.json
$ stixforge validate bundle.json
$ stixforge validate bundle.json --external --json
$ stixforge validate bundle.json --today 2027-01-01   # report expired indicators
```

Exit codes follow the house contract: `0` valid, `1` a high finding, `2` it could not check
(file unreadable, or no external checker installed). *Not checked is not clean.*

With `--external`, two checkers are used when available:

- **`stix2`** (the OASIS library) parses the bundle against its object model. Needs no network.
- **`stix2-validator`** validates against the JSON schemas. It needs its schema cache, which it
  downloads; without that cache it cannot say anything, and the run reports
  `external-not-checked` instead of inventing a verdict.

## Method

Four rules, and the tool enforces all four:

1. **No author, no bundle** (`ValueError`): a product that does not say who says it is not
   intelligence, it is a rumour.
2. **No `created`, no bundle.** Identifiers come from content; a clock-derived timestamp
   would produce the same id with different content on every build. Rebuilds are identical.
3. **No marking, no sharing.** Every SDO carries `object_marking_refs`, and the marking is
   one of the **official TLP 2.0** objects (OASIS common objects): `CLEAR`, `GREEN`, `AMBER`,
   `AMBER+STRICT`, `RED`. `TLP:WHITE` is TLP 1.0 and is refused, not silently renamed.
4. **Observables are immutable.** In STIX 2.1 a cyber-observable carries no `created`,
   `modified`, `created_by_ref` or marking of its own — adding them makes the bundle invalid
   for `stix2.parse`. This was found by validating with the real library, not by reading the
   spec.

**The gate bites.** The worked example ships as `TLP:AMBER`. With `TLP:CLEAR` the bundle
builds and passes its own validation; `sharegate` then reports whether the content looks
sensitive. That is the intended relationship between the two tools.

## Licence

MIT — see [LICENSE](https://github.com/Falsifyer/Defensible-CTI/blob/main/LICENSE).

---

**Martín Eliseo** — cyber threat intelligence.
[GitHub](https://github.com/Falsifyer) · [falsifyer.github.io](https://falsifyer.github.io)
