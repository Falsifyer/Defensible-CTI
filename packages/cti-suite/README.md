# cti-suite (package)

**The cycle as one artifact, and one MCP server instead of six.**

The six tools stay separate and installable on their own. This package adds the two
things that only work when the six are together:

| Command | What it does |
|---|---|
| `ctisuite report` | renders requirement, judgement, evidence, hunt plan and marking as one markdown product |
| `ctisuite-mcp` | one MCP server with prefixed tools for the whole cycle |

## Report

```console
$ ctisuite report \
    --pir demo/pir.json \
    --assessment demo/assessment.json \
    --verdict demo/out/judgement.json \
    --hunt demo/out/hunt.json \
    --product demo/product.json \
    --bundle demo/out/bundle.json \
    -o demo/out/product.md
```

Nothing in the report is computed from thin air: the ceiling and the ranking come from the
judgement, the ranking's supporting evidence from the dossier, the trace from the STIX
`external_references`, and anything missing is listed as a gap.

## One MCP server

The six packages each ship their own MCP server. Registering all six means six servers
with three tools called `validate` and two called `assess`. `ctisuite-mcp` exposes them
with prefixes instead:

`pir_validate_register`, `cryptonym_assess`, `assessment_assess`, `huntplan_validate`,
`huntplan_detections`, `stixforge_build`, `stixforge_validate`, `sharegate_check`, and the
cross-cutting `suite_report`.

Each tool calls the same function the CLI calls; nothing is reimplemented here.

## Install

```console
$ uv sync --all-packages --all-extras
$ ctisuite --version
```

## Licence

MIT. See [`../../LICENSE`](https://github.com/ME0094/cti-suite/blob/main/LICENSE).
