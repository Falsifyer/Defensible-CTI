# pir-ledger

**A PIR that does not name the decision it informs is not a PIR: it is a topic of interest.**

`pir validate` rejects the whole register when a requirement does not say which decision someone
takes with the answer, who takes it, or what would prove it answered. The validator does not judge
the content: it checks that the question is tied to a decision and that collection has a graded
closure criterion.

## What it is

A register of **PIR → EEI → indicator** in one JSON file, plus a tool that audits it:

- **PIR** — a question tied to a decision, with its consumer, its priority and its deadline.
- **EEI** — the essential elements of information needed to answer it.
- **Indicator** — what would be observed, with its source graded on the Admiralty scale (`B2`).

Subcommands: `pir validate` (audits) and `pir list` (what exists, for which decision, and how long is
left).

## What it is not

- **Not an IOC feed.** It does not collect, enrich or call any API: indicators are cited, not ingested.
- **Not a case manager** and not a dashboard. It holds no state of its own: the register is the file,
  and the file is versioned.
- **It does not set priorities.** It checks that the priority is one of three and that a deadline
  exists; which one applies is the consumer's call.

## Install

```console
$ pip install -e '.[dev]'      # development
$ pip install .                # use
```

No runtime dependencies: Python 3.11 or newer and the standard library.

## Use

```console
$ pir validate examples/pir.json
$ pir validate examples/pir.json --json | jq .valid
$ pir list examples/pir.json --today 2026-10-22
```

The exit code is the contract: `0` valid register, `1` a high finding, `2` the file could not be read.
A register with a single requirement lacking a decision exits with `1` and names it.

## Method

The register is written in `examples/pir.json`; the format is described in
[`docs/register.md`](docs/register.md). Three rules, and the validator checks them:

1. **No decision, no PIR** (`no-decision`, high). This is the one that holds the rest up.
2. **No consumer, no decision** (`no-consumer`, high): a person or a team, by name.
3. **No graded indicator, no closure criterion** (`indicator-ungraded`, high; `bad-admiralty`,
   medium when the grade is not `A-F` + `1-6`).

Warnings that do not invalidate the register: a question that does not end in `?`
(`not-a-question`), a priority outside `high|medium|low` (`bad-priority`), a deadline in the past
with no answer (`stale`), a duplicate identifier (high) and an EEI without indicators (medium).

## Licence

MIT. See [`LICENSE`](LICENSE).

---

**Martín Eliseo** — cyber threat intelligence.
[GitHub](https://github.com/ME0094) · [me0094.github.io](https://me0094.github.io)
