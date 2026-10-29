# External corpus

**Scaffolding only.** There are no real cases here yet. This directory exists so that the
first external case is collected under a protocol, not improvised alongside the engine.

- [`PROTOCOL.md`](PROTOCOL.md) — roles, blindness, source independence, standards,
  disagreement, split, pre-registration, metrics and ethics.
- [`schema.json`](schema.json) — the JSON Schema every case must satisfy.
- [`case.template.json`](case.template.json) — a placeholder case. It is **not** a case and
  must not be added to a corpus as one.
- [`validate_external.py`](validate_external.py) — the executable checklist: schema,
  placeholders, two adjudicators, two independent sources and the adjudication filter.

## Files a real corpus will have

```text
external/
  PROTOCOL.md
  schema.json
  case.template.json
  validate_external.py
  corpus.json          # created from real, adjudicated cases
  expected.json        # generated once the split is frozen and the engine is run
```

`corpus.json` and `expected.json` are deliberately absent. Creating either before the
protocol is accepted and the cases are adjudicated would be the failure this scaffold is
meant to prevent.

## Validate a case or corpus

From `packages/cryptonym`:

```console
$ python - <<'PY'
import json, jsonschema
schema = json.load(open("evaluation/external/schema.json"))
jsonschema.Draft202012Validator.check_schema(schema)
jsonschema.Draft202012Validator(schema).validate(
    json.load(open("evaluation/external/case.template.json"))
)
print("schema and template are valid")
PY
```

Once `corpus.json` exists, run the executable checklist, then the evaluator:

```console
$ python evaluation/external/validate_external.py evaluation/external/corpus.json
$ python evaluation/run_evaluation.py --adjudicated evaluation/external/corpus.json --check --strict
```

`validate_external.py` exits 2 if it cannot read the corpus or the schema, 1 on a high
finding (placeholder, one adjudicator, one source, unearned truth), and 0 only when the
checklist is clean.

`--strict` fails if a binary truth was not earned from independent sources. `--check`
compares the projection with `expected.json`; generate that file only after the held-out
split is frozen.

## The rule that matters

A case is not external because its file lives in this directory. It is external when:

1. two adjudicators, neither the author, decided it independently;
2. the source graph is recorded (`publisher`, `url`, `category`, `kind`, `derived_from`);
3. a binary truth has two independent sources asserting it, or is `contested`;
4. the split was committed before the first engine run;
5. the denominator (`calls`, `abstentions`, `unsupported`) is published with the metric.

See [`PROTOCOL.md`](PROTOCOL.md) for the full checklist.
