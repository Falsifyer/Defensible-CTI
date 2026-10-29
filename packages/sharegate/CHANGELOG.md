# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## Unreleased

### Fixed

- **A corrupt `.json` bundle is `checked: false` and exit 2**, not a text product with
  `shareable: true`. The text rule still applies to files that are not JSON.
- **Unmarked content SDOs are refused**: `infrastructure`, `note`, `attack-pattern` and
  `relationship` no longer slip through the old whitelist.
- **Unmarked text is refused too**: `tlp-missing` is now a high finding, not a medium warning;
  silence is not `TLP:CLEAR`.

## 0.2.0 — 2026-10-22

### Changed

- **One validator.** The structural STIX check delegates to `cti_method.stix.validate_bundle`,
  the same function `stixforge` uses; the two tools can no longer disagree.
- **Markings are resolved from `object_marking_refs`**, not from a regex over the serialised
  document: a marking defined but not referenced no longer counts, and a `TLP:CLEAR` bundle
  full of IP observables is no longer refused.
- The sensitive-content heuristic is a **medium** guard (it surfaces, it does not block), and
  it reads only fields a human wrote.
- TLP 2.0 labels: `CLEAR`, `GREEN`, `AMBER`, `AMBER+STRICT`, `RED`; `TLP:WHITE` is flagged as
  deprecated.
- An unreadable file exits **2** (`cannot check`), not 1.

- `--today` checks indicator expiry; a bundle whose indicators have **all** expired is not
  shareable (`stix-all-indicators-expired`).
- A bundle over the object limit reports `checked: false` and exits 2 instead of walking it.


## 0.1.0 — 2026-10-22

First version published as a release. The repository has existed since 2026-10-09.

- First release: `sharegate check` validates a product or a STIX bundle against the TLP 2.0 policy and external schemas.
- `sharegate tlp` checks the marking alone; `sharegate policy` prints the table.
- The same gate is exposed as an MCP tool.
