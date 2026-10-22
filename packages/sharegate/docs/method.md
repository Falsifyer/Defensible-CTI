# Method

## Scope

A pre-share gate for CTI products: verify the **TLP** marking and the **STIX 2.1**
structure before disclosure. The gate is deliberately objective — it checks a product
against published rules, not against a preference.

## Ground truth

| Check | Standard |
|---|---|
| TLP levels, ranks and meanings | FIRST **TLP 2.0** (CLEAR / GREEN / AMBER / AMBER+STRICT / RED; WHITE deprecated) |
| STIX object identity and structure | **STIX 2.1** (bundle shape, `type--uuid` ids, `spec_version`) |

Because the truth is a schema, the evaluation is not a judgement: a known-bad bundle
produces a known finding code. See `tests/test_core.py`.

## Rules applied

- **TLP missing** → medium. A product without a handling caveat cannot be shared safely.
- **TLP conflicting** (two different levels) → high. The gate refuses to guess.
- **TLP:WHITE** → low. Deprecated; recommend `TLP:CLEAR`.
- **Permissive marking on sensitive content** (CLEAR/GREEN with IPs, emails or sensitive
  terminology) → high. The most common real leak.
- **STIX**: non-bundle, no `objects`, missing type/id, id/type mismatch, duplicate id →
  high; wrong `spec_version` → medium; missing → low.

`shareable` is false only on a **high**-severity finding; lower findings are surfaced but
do not block.

## What it does not do

- It does not validate every normative STIX constraint (use `stix2`).
- Its sensitive-content heuristic is a guard, not a classifier; it can miss and can
  over-flag, and it says so.
