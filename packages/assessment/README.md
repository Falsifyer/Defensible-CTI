# assessment-mcp

**A ledger of graded judgements.** Any claim — not just actor aliases — gets the same
discipline: evidence typed by diagnostic strength, competing hypotheses compared by
least-inconsistency, **two axes** of confidence, a **ceiling derived from the evidence**, and
an **external truth that must be earned** from independent sources.

Built on the shared core, [`cti-method`](../cti-method/README.md): the core owns grading,
adjudication and evaluation; this tool owns the general workflow and a persistent ledger of
the judgements.

> A merge is a hypothesis, not a fact — and so is every other claim.

## What it refuses

- A claim with **no declared grade** (`no-grade`): there is no silent default to `low`.
- A grade **above the ceiling** the evidence supports (`grade-exceeds-evidence`). `high`
  needs a diagnostic discriminating item and two independent sources; shared tradecraft
  alone cannot exceed `low`.
- A comparison with **one hypothesis** (`no-hypotheses`): one option is not analysis.
- A claim whose declared sources derive from one another: independence is structural, not
  typographic, so a derived source does not raise the ceiling.
- A ledger entry that was edited after it was written: `ledger --verify` reports the line.

## What it is not

- **Not a knowledge base.** It grades claims and keeps a ledger; sourcing is yours.
- **Not a decision.** It states a graded judgement and what would change it, not a verdict.
- **Not truth.** An "admissible" truth means independent sources asserted it, not that it is right.

## Install

```bash
uv sync --all-packages --all-extras     # inside the suite
pip install -e ../cti-method -e .       # on its own
```

There is no dependency on the alias package: this tool works on any claim.

## Use

```bash
assessment grade --confidence moderate --probability likely
assessment assess claim.json --register pir.json --against judgement.json --append ledger.jsonl
assessment assess claim.json --strict                # validate the verdict against its schema
assessment ledger ledger.jsonl --verify
```

`--now 2026-10-22T00:00:00Z` on `assess` writes the ledger entry at a fixed instant, so two
runs of the same claim produce the same ledger.`

`assess --against` re-derives the previous step's judgement and reports `judgement-mismatch`
if the dossier changed after it was produced. `--register` verifies the `requirement_id`
against the PIR register. `--append` writes the verdict to a hash-chained ledger.

## As an MCP server

```bash
assessment-mcp
```

Tools: `grade_claim`, `weigh_evidence`, `grade_ceiling`, `filter_external_truth`,
`assess_document`, `append_claim_to_ledger`, `read_ledger_file`, `verify_ledger_file`,
`calibrate_cases`, `method_docs`.

## The ledger

Each line is an entry with `seq`, `created_at`, `tool`, `claim_id`, `claim_hash`, `claim`,
`prev_hash` and `hash`; the schema is `ledger-entry` in `cti-method`. The hash covers the entry without itself; `prev_hash` chains to the
previous line. Editing a claim, dropping a line or reordering two lines breaks the chain at a
known index.

## Method

See [docs/method.md](src/assessment/docs/method.md).

## License

MIT — see [LICENSE](https://github.com/Falsifyer/Defensible-CTI/blob/main/LICENSE).

---

**Martín Eliseo** — cyber threat intelligence.
[GitHub](https://github.com/Falsifyer) · [falsifyer.github.io](https://falsifyer.github.io)
