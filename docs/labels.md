# Issue labels

The repository uses one axis for kind and one for priority. Create them once with the
commands below; the issue templates pre-fill `bug` and `enhancement`.

| Label | Meaning |
|---|---|
| `bug` | a tool behaves differently from what its README claims |
| `enhancement` | a refusal or a check that should exist |
| `contract` | changes findings, exit codes, a schema or TLP handling — needs a `schema_version` bump |
| `method` | changes the ceiling, the ACH weighting, the adjudication filter or the evaluation |
| `docs` | documentation only |
| `ci` | workflows, release, dependency automation |
| `p0` | the README makes a claim the code does not keep |
| `p1` | product: the cycle is harder to use than it should be |
| `p2` | engineering or security hardening |
| `p3` | documentation and governance |

```console
$ for l in bug enhancement contract method docs ci p0 p1 p2 p3; do
    gh label create "$l" --repo ME0094/cti-suite 2>/dev/null || true
  done
```

Anything labelled `contract` should be reviewed against
[`docs/roadmap.md`](roadmap.md) and the schemas before merging.
