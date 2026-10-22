# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## 0.2.0 — 2026-10-22

### Changed

- **Official TLP 2.0 markings** from the OASIS common objects: `TLP:CLEAR` and
  `TLP:AMBER+STRICT` are first-class; `TLP:WHITE` is refused, never emitted.
- **`created` is required.** Identifiers are content-derived, so a clock-derived timestamp
  produced the same id with different content on every build. Rebuilding is now
  byte-identical.
- **Traceability:** `--requirement`, `--assessment` and `--hunt` verify the ids the product
  cites and emit them as `external_references` on the report.
- The factory validates its own output and refuses to write an invalid bundle.
- `valid_until` and `confidence` are emitted when supplied; `validate --today` reports
  expired indicators.
- The structural validator moved to `cti-method`; codes are unified (`stix-*`).

- `valid_until` from the product now defaults onto indicators (where STIX allows it) instead
  of the report (where it does not, and `stix2` rejected it).
- A product may pin `assessment_hash` / `hunt_hash` / `requirement_hash`; a mismatch is
  `trace-hash-mismatch` and the build is refused. References travel as `<id>@<sha256:12>`.


## 0.1.0 — 2026-10-22

- `stixforge build`: product JSON to STIX 2.1 bundle — marking-definition, identity, cyber-observables,
  indicators, malware objects and a report referencing them. Deterministic identifiers.
- `stixforge validate`: identifier shape and type, unresolved references, duplicate identifiers,
  unmarked SDOs, missing specification version.
- `--external`: runs the OASIS `stix2` library and `stix2-validator` when installed; reports
  `external-not-checked` when the validator has no schema cache instead of inventing a verdict.
- Validated end to end against `sharegate`: an amber bundle is shareable, a clear one with
  infrastructure in it is rejected.
