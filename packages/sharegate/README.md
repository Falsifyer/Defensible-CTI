# ShareGate

**A pre-share compliance gate for CTI: is the TLP right, and is the STIX well-formed?**

> Shareable is a claim. Prove it.

Before a product or a STIX bundle leaves the building, ShareGate answers two objective
questions and blocks on the ones that matter:

- **TLP 2.0** (FIRST): missing marking, conflicting markings, deprecated `TLP:WHITE`, and a
  permissive marking (`CLEAR`/`GREEN`) on content that looks sensitive.
- **STIX 2.1**: a non-bundle top level, a missing `objects` array, objects without a type
  or id, an id whose prefix does not match its type, duplicate ids, and a wrong or missing
  `spec_version`.

The ground truth is **external and citable** — the FIRST TLP 2.0 definitions and the STIX
2.1 specification — so this gate is judged against a standard, not an opinion.

## What it is not

- **Not a full STIX validator.** It checks structure, not every normative constraint; use
  `stix2` validation for the rest.
- **Not a DLP.** The sensitive-content heuristic is a guard, not a classifier.
- **Not a policy engine.** It applies the TLP and STIX rules; your handling policy is yours.

## Install and use

```bash
pip install -e '.[mcp]'
sharegate policy
sharegate tlp product.md
sharegate check bundle.json       # exit 1 if not shareable
```

## As an MCP server

```bash
sharegate-mcp
```

Tools: `tlp_policy_table`, `check_tlp_marking`, `check_stix_bundle`, `pre_share_check`.

## Structure

```
src/sharegate/
  core.py       the gate: TLP 2.0 checks, STIX 2.1 checks, pre-share aggregate
  cli.py        command-line interface
  mcp_server.py MCP tools
```

## License

MIT — see [LICENSE](LICENSE).

---

**Martín Eliseo** — cyber threat intelligence.
