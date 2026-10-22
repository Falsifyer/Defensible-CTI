# Method and corrections

How judgements in Cryptonym are produced, graded and corrected. It is stated so a reader
can judge the outputs against a declared standard rather than trust the code.

## Scope

Actor alias reconciliation: the question of whether two vendor designations refer to
the same actor. Every assessment states its boundary — what is observed, what is
inferred, and what could not be verified.

## A merge is a hypothesis

A platform that stores aliases as a flat list turns a *hypothesis* into a *fact* the
moment it is written. Cryptonym does not collapse anything. It records:

- **designations** — one vendor's name, kept separate;
- **evidence** — typed items, each graded against every hypothesis;
- **assessments** — the graded, versioned judgement that links two designations;
- **linkages** — graded edges between designations, consumed at an explicit threshold.

Lowering the threshold can split a cluster again: the edges were never lost.

## Diagnostic vs non-diagnostic evidence

The most common way alias work goes wrong is treating shared tradecraft as proof of
identity. Two actors can share tooling, binaries and C2 paths without being one
organisation. Cryptonym therefore classifies evidence:

| Diagnostic (can support identity) | Non-diagnostic (cannot, alone) |
|---|---|
| infrastructure, code, operator artefacts | tactics/TTPs, targeting, generic reporting |

Non-diagnostic items that are consistent with every hypothesis are surfaced explicitly
so they are not mistaken for support.

## The grade is capped by the evidence

A dossier declares a confidence, but the evidence sets a **ceiling** on it:

| Ceiling | Requires |
|---|---|
| `low` | no diagnostic item discriminates; shared tradecraft and non-diagnostic overlap cannot carry more |
| `moderate` | at least one diagnostic item discriminates, all from one source |
| `high` | at least one diagnostic item discriminates **and** two independent sources contribute diagnostics |

A grade below the ceiling is allowed (an analyst may be more cautious). A grade above it is
`grade-exceeds-evidence` and `cryptonym assess` exits 1. A dossier with no declared grade is
`no-grade`, also high: there is no silent default to `low`. Independence is by source
string, normalised — coarse, checkable, and it fails closed — so a dossier that needs finer
independence should model its sources as sources.

This is also what the evaluation harness calibrates: the **derived** ceiling, not the
declared prose. The current golden-pair corpus declares more than its evidence supports in
five of ten cases, and the harness prints that count instead of hiding it.

## Analysis of Competing Hypotheses

Evidence is tested against the competing hypotheses at once — *same actor*, *distinct
but overlapping*, *brokered / shared access*. The favoured hypothesis is the one with
the **least inconsistent** evidence, not the one with the most supporters. Ties are
broken deterministically, not by strength of feeling.

## Two-axis grading

Every judgement carries two independent axes, per claim, not per section:

- **Confidence** — how good the sourcing and reasoning are: **high** (two or more
  independent authoritative sources), **moderate** (one credible source, or
  corroboration with gaps), **low** (single-source, self-claimed, inferential).
- **Probability** — how likely the estimated outcome is, stated only where the claim is
  estimative: *nearly certain*, *very likely*, *likely*, *roughly even chance*,
  *unlikely*, *very unlikely*.

A claim can be *very likely* at *low confidence* (a single source) or *roughly even* at
*high confidence* (strong data, genuine uncertainty).

## Review — stated honestly

Assessments are **single-author** unless a revision records otherwise. They are **not**
presented as peer-reviewed, because no second qualified analyst signs them. What exists
is a self-check against the standards above and an open invitation to challenge.

## Versioning and corrections

Each assessment carries a **version**, a **date** and a **review trigger**. A correction
that changes a judgement is published as a **new version**, never as a silent edit.

## Handling

Assessments are **TLP:CLEAR** (TLP 2.0) unless marked otherwise.

## Related

- [Architecture](architecture.md)
- [Data model](data-model.md)
- [Evaluation](evaluating-alias-reconciliation.md)
