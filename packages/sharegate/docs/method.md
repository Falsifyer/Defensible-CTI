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
  terminology) → **medium**. It is a heuristic guard, and a heuristic does not get to
  refuse a product. For a STIX bundle it reads only fields a human wrote: an IP inside a
  cyber-observable is an indicator, not a confession.
- **STIX** → whatever the suite's single validator says (`cti_method.stix.validate_bundle`),
  because the factory and the gate must not disagree: structural breakage, a missing
  marking, an unresolved reference, a duplicate id or a wrong `spec_version` → high; no
  marking definition, an unknown marking or an expired indicator → medium; deprecated
  `TLP:WHITE` → low.

## How the marking is read

For a STIX bundle, from `object_marking_refs` and the marking definitions the bundle
contains — not from a regex over the serialised document. A marking that is defined but
never referenced does not travel with the content, so it does not count; two marked objects
that reference different labels are a conflict. For plain text, the labels are read from the
text.

`shareable` is false only on a **high**-severity finding; lower findings are surfaced but
do not block.

## What it does not do

- It does not validate every normative STIX constraint (use `stix2`).
- Its sensitive-content heuristic is a guard, not a classifier; it can miss and can
  over-flag, and it says so. It never blocks on its own.
