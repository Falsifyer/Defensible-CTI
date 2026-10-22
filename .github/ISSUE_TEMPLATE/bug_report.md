---
name: Bug report
about: Something in one of the tools behaves differently from what it claims
labels: bug
---

## Which package

<!-- cti-method, cryptonym, assessment, sharegate, stixforge, pir, huntplan, cti-suite -->

## What you ran

```console
$ ...
```

## What happened

<!-- Paste the output. The exit code matters: 0 clean, 1 a high finding, 2 could not check. -->

```console
$ echo $?
```

## What you expected

## Versions

```console
$ uv run <command> --version
$ python --version
```

## Does `make demo` still pass?

<!-- If the demo fails, say so: it narrows the problem to the chain. -->
