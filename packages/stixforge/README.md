# stix-forge

**A bundle is not shareable until it says how far it may travel.**

`stixforge build` turns an intelligence product into a STIX 2.1 bundle with the TLP marking, the
author's identity, the observables, the indicators and a `report` that references all of them.
`stixforge validate` checks the result, and with `--external` hands it to the OASIS tooling.

The bundle is **deterministic**: the same product produces the same identifiers, so rebuilding it
does not fork the same objects into two versions.

## What it is

- **A producer.** Product JSON in, STIX 2.1 bundle out: marking-definition, identity, SCOs,
  indicators, malware objects and a report with `object_refs`, all with `created_by_ref` where it
  applies.
- **A validator.** Structural checks (identifier shape and type, references that resolve, no
  duplicate identifiers, every SDO carrying a marking) plus, with `--external`, the OASIS library
  and `stix2-validator`.
- **The other half of `sharegate`.** `sharegate` is the gate that decides whether a bundle may leave;
  this is the factory that builds one worth gating.

## What it is not

- **Not another OpenCTI.** No web UI, no ingestion, no correlation, no database.
- **No TAXII yet.** TAXII 2.1 publication is deliberately out of 0.1.0; the bundle is the unit.
- **It does not judge the analysis.** It checks that the product says who says it, what it claims
  and how far it travels — not whether the claim is true.

## Install

```console
$ pip install -e '.[dev]'          # development and tests
$ pip install -e '.[dev,external]' # plus stix2 and stix2-validator for --external
```

No runtime dependencies: Python 3.11 or newer and the standard library.

## Use

```console
$ stixforge build examples/product.json -o bundle.json
$ stixforge validate bundle.json
$ stixforge validate bundle.json --external --json
```

Exit codes follow the house contract: `0` valid, `1` a high finding, `2` it could not check (file
unreadable, or no external checker installed). *Not checked is not clean.*

With `--external`, two checkers are used when available:

- **`stix2`** (the OASIS library) parses the bundle against its object model. Needs no network.
- **`stix2-validator`** validates against the JSON schemas. It needs its schema cache, which it
  downloads; without that cache it cannot say anything, and the run reports `external-not-checked`
  instead of inventing a verdict.

## Method

Three rules, and the tool enforces the first two:

1. **No author, no bundle** (`ValueError`): a product that does not say who says it is not
   intelligence, it is a rumour.
2. **No marking, no sharing.** Every SDO carries `object_marking_refs`; `validate` fails a bundle
   where an indicator, malware object or report is unmarked.
3. **Observables are immutable.** In STIX 2.1 a cyber-observable carries no `created`, `modified`,
   `created_by_ref` or marking of its own — adding them makes the bundle invalid for `stix2.parse`.
   This was found by validating with the real library, not by reading the spec.

The TLP markings are the four in the STIX 2.1 specification, with their canonical identifiers.
TLP 2.0 (`clear`, `amber+strict`) is not in the specification's appendix, so `clear` maps to the
specification's `TLP:WHITE` object and the README says so instead of inventing identifiers.

**The gate bites.** The worked example ships as `TLP:AMBER`. With `TLP:CLEAR` the bundle builds and
passes its own validation, and `sharegate` rejects it: *permissive marking on content that looks
sensitive*. That is the intended relationship between the two tools, and it is why the example is
amber.

## Licence

MIT. See [`LICENSE`](LICENSE).

---

**Martín Eliseo** — cyber threat intelligence.
[GitHub](https://github.com/ME0094) · [me0094.github.io](https://me0094.github.io)
