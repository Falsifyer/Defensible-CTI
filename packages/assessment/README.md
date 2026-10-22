# assessment-mcp

**A ledger of graded judgements.** Any claim — not just actor aliases — gets the same
discipline: evidence typed by diagnostic strength, competing hypotheses compared by
least-inconsistency, **two axes** of confidence, and an **external truth that must be
earned** from independent sources.

This is the real consumer of the shared core, [`cryptonym.method`](https://github.com/ME0094/cryptonym):
the core owns grading, adjudication and evaluation; this tool owns the general workflow
and a persistent ledger of the judgements.

> A merge is a hypothesis, not a fact — and so is every other claim.

## What it is not

- **Not a knowledge base.** It grades claims and keeps a ledger; sourcing is yours.
- **Not a decision.** It states a graded judgement and what would change it, not a verdict.
- **Not truth.** An "admissible" truth means independent sources asserted it, not that it is right.

## Install

```bash
# the shared core first (editable, or from the private repo with a read-only token)
pip install -e /root/cryptonym
# pip install "cryptonym @ git+https://x-access-token:<TOKEN>@github.com/ME0094/cryptonym.git@v0.6.0"

pip install -e '.[mcp]'
```

## Use

```bash
assessment grade --confidence moderate --probability likely
assessment assess claim.json
assessment ledger ~/ledger/claims.jsonl
```

## As an MCP server

```bash
assessment-mcp
```

Tools: `grade_claim`, `weigh_evidence`, `filter_external_truth`, `assess_document`,
`append_claim_to_ledger`, `read_ledger_file`, `calibrate_cases`, `method_docs`.

## Method

See [docs/method.md](docs/method.md).

## License

MIT — see [LICENSE](LICENSE).

---

**Martín Eliseo** — cyber threat intelligence.
