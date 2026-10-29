# Schemas

The six artifacts are the API of this suite. Their schemas ship **with the shared core**,
so they are available on any machine where the tools are installed:

```python
from cti_method import schema as schemas
schemas.document("assessment")          # the schema as a dict
schemas.validate(document, "assessment")  # needs the 'schemas' extra
```

They live in
[`packages/cti-method/src/cti_method/schemas/`](../packages/cti-method/src/cti_method/schemas).
There is no second copy under `/schemas`: each schema's `$id` is the `raw.githubusercontent.com`
URL of that file, so a consumer can fetch what the document cites.

| File | Schema | Produced by | Consumed by |
|---|---|---|---|
| `pir.json` | `pir` | you | `pir validate`, `assessment assess --register` |
| `assessment.json` | `assessment` | you | `cryptonym assess`, `assessment assess` |
| `hunt.json` | `huntplan` | you (validated by `huntplan`) | `stixforge build --hunt` |
| `product.json` | `product` | you | `stixforge build` |
| judgement (stdout) | `judgement` | `cryptonym assess`, `assessment assess` | your pipeline, `--strict` |
| ledger line | `ledger-entry` | `assessment assess --append` | `assessment ledger`, `--verify` |
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

The reference is `<id>@<sha256:12>`: the hash is the hash of the exact upstream content. A
document may also record `<kind>_hash`; when it does, a mismatch is `trace-hash-mismatch`
and the build is refused. An edited dossier no longer keeps the same identity silently.

## Validate

```console
$ python -c "import json, jsonschema; jsonschema.validate(json.load(open('demo/pir.json')), json.load(open('packages/cti-method/src/cti_method/schemas/pir.schema.json')))"
$ uv run assessment assess demo/assessment.json --strict
```

`jsonschema` is an extra, not a runtime dependency: the tools validate semantics, the
schemas pin the shape, and `--strict` reports that it could not check when the extra is
absent.

## Versioning

`schema_version` is `1.0` for every format. A breaking change to a field bumps it and the
schemas are updated in the same commit; the reader checks the field, not the repository
history.
