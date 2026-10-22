# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## 0.1.0 — 2026-10-22

- `stixforge build`: product JSON to STIX 2.1 bundle — marking-definition, identity, cyber-observables,
  indicators, malware objects and a report referencing them. Deterministic identifiers.
- `stixforge validate`: identifier shape and type, unresolved references, duplicate identifiers,
  unmarked SDOs, missing specification version.
- `--external`: runs the OASIS `stix2` library and `stix2-validator` when installed; reports
  `external-not-checked` when the validator has no schema cache instead of inventing a verdict.
- Validated end to end against `sharegate`: an amber bundle is shareable, a clear one with
  infrastructure in it is rejected.
