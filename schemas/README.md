# Schemas

The six artifacts are the API of this suite. These schemas pin their shape, and the demo
documents carry `$schema` and `schema_version` so a consumer can check a file before using
it.

| File | Schema | Produced by | Consumed by |
|---|---|---|---|
| `pir.json` | [`pir.schema.json`](pir.schema.json) | you | `pir validate`, `assessment assess --register` |
| `assessment.json` | [`assessment.schema.json`](assessment.schema.json) | you | `cryptonym assess`, `assessment assess` |
| `hunt.json` | [`huntplan.schema.json`](huntplan.schema.json) | you (validated by `huntplan`) | `stixforge build --hunt` |
| `product.json` | [`product.schema.json`](product.schema.json) | you | `stixforge build` |
| `bundle.json` | STIX 2.1 | `stixforge build` | `sharegate check` |
| `product.md` | — | `ctisuite report` | a human |

## The chain

```
requirement_id          assessment_id            hunt_id
     │                        │                     │
  pir.json ───────────► assessment.json ─────► hunt.json ─────► product.json
                                                                     │
                                                                     ▼
                                                                 bundle.json
```

Every downstream document may cite the one before it, and when the upstream file is
supplied the citing id is **verified against it**, never trusted as text:

- `assessment assess --register pir.json` — `requirement_id` must exist in the register;
- `huntplan validate hunt.json --assessment verdict.json` — `assessment_id` must match;
- `stixforge build product.json --requirement pir.json --assessment verdict.json --hunt hunt.json`
  — all three are verified, and the bundle carries them as `external_references`.

A mismatch is a high finding (`trace-mismatch`, `trace-unknown-requirement`): the chain is
broken, not amended.

## Validate

```console
$ python -c "import json, jsonschema; jsonschema.validate(json.load(open('demo/pir.json')), json.load(open('schemas/pir.schema.json')))"
```

`jsonschema` is a test dependency, not a runtime one: the tools validate semantics, the
schemas document the shape.

## Versioning

`schema_version` is `1.0` for every format. A breaking change to a field bumps it and the
schemas are updated in the same commit; the reader is expected to check the field, not the
repository history.
