# ShareGate

**A pre-share compliance gate for CTI: is the TLP right, and is the STIX well-formed?**

> Shareable is a claim. Prove it.

Before a product or a STIX bundle leaves the building, ShareGate answers two objective
questions and blocks on the ones that matter:

- **TLP 2.0** (FIRST): missing marking, conflicting markings, deprecated `TLP:WHITE`, and a
  permissive marking (`CLEAR`/`GREEN`) on content that looks sensitive.
- **STIX 2.1**: the structural check, **imported from [`cti-method`](../cti-method/README.md)**
  — the same function `stixforge` calls. One validator, one severity table, no room for the
  factory and the gate to disagree.

The ground truth is **external and citable** — the FIRST TLP 2.0 definitions and the STIX
2.1 specification — so this gate is judged against a standard, not an opinion.

## How the marking is read

From `object_marking_refs`, not from a regex over the serialised document:

- a marking definition that nothing references does **not** travel with the content and does
  not count;
- two marked objects that reference different labels are a **conflict** (high);
- `TLP:CLEAR` on a bundle of IP observables is **not** a leak: an indicator is not a
  confession. The sensitive-content heuristic reads only fields a human wrote, and it is a
  **medium** guard — it surfaces, it does not block.
- **Expiry**: with `--today`, an expired indicator is a medium finding, and a bundle whose
  indicators have *all* expired is not shareable — it is not intelligence any more.

## What it is not

- **Not a full STIX validator.** It checks structure and marking; use `stix2` validation for
  the rest.
- **Not a DLP.** The sensitive-content heuristic is a guard, not a classifier.
- **Not a policy engine.** It applies the TLP and STIX rules; your handling policy is yours.

## Install and use

```bash
pip install -e ../cti-method -e '.[mcp]'
sharegate policy
sharegate tlp product.md
sharegate check bundle.json                 # exit 1 if not shareable, 2 if it cannot be read
sharegate check bundle.json --today 2027-01-01   # also report expired indicators
```

## As an MCP server

```bash
sharegate-mcp
```

Tools: `tlp_policy_table`, `check_tlp_marking`, `check_stix_bundle`, `pre_share_check`. The
suite's facade (`ctisuite-mcp`) exposes the same gate as `sharegate_check`.

## Structure

```
src/sharegate/
  core.py       the gate: TLP 2.0 checks, pre-share aggregate, the shared STIX validator
  cli.py        command-line interface
  mcp_server.py MCP tools
```

## License

MIT — see [LICENSE](https://github.com/Falsifyer/Defensible-CTI/blob/main/LICENSE).

---

**Martín Eliseo** — cyber threat intelligence.
[GitHub](https://github.com/Falsifyer) · [falsifyer.github.io](https://falsifyer.github.io)
