# Vendored STIX 2.1 JSON Schemas

These schemas come from
[`oasis-open/cti-stix2-json-schemas`](https://github.com/oasis-open/cti-stix2-json-schemas),
`stix2.1` branch. They are vendored so `stixforge validate --external` can run offline,
without the schema cache that `stix2-validator` otherwise downloads.

- **Licence:** BSD-3-Clause. The original licence is in [`LICENSE`](LICENSE); the
  copyright notice and disclaimer are retained.
- **Scope:** `common/`, `sdos/`, `sros/` and `observables/`. Examples, interop and pattern
  grammar are not vendored because they are not needed to validate a bundle.
- **Update:** copy the same four directories from the upstream `stix2.1` branch, keep
  `LICENSE`, and run the stixforge tests. The `$id` values already point at the upstream
  raw URLs, so `$ref` resolution is local and stable.
