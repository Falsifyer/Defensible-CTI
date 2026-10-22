# Adjudication: external truth, independence and disagreement

The evaluation is only as honest as its truth. If the truth is the author's own
assertion, the accuracy figures measure agreement with the author, not with reality.
This document is the standard the **adjudicated corpus** is held to, and
`cryptonym.evaluate.adjudication` is that standard made executable.

## Truth vocabulary

| Truth | Meaning | Enters the error rates? |
|---|---|---|
| `same_actor` | The two designations name the same actor | **yes** |
| `distinct` | They are not the same actor | **yes** |
| `contested` | Sources genuinely disagree, or scope is unresolved | no — reported as coverage |
| `unadjudicated` | Too thin, or no independent source asserts a stance | no — reported as coverage |

There is no "leaning same". A truth is binary and earned, or it is not a truth.

## Standards of evidence

| Standard | What it means | Minimum independent sources |
|---|---|---|
| `author-assertion` | The project says so | — (never admissible) |
| `single-source` | One source says so | — (never admissible) |
| `vendor-consensus` | Two or more independent vendors agree | 2 |
| `government-statement` | An authoritative government source asserts it | 1 government **+ 1 corroborating** |
| `independent-corroboration` | Two or more independent sources assert it | 2 |

A government name-list alone does **not** settle a disputed alias: `government-statement`
still requires a corroborating independent source. This is deliberate — the whole reason
Cryptonym exists is that an alias list is weaker than an identity claim.

## Independence

Two sources are not two voices if they are the same publisher or if one derives from the
other. A source that declares `derived_from` a publisher present in the case, or a second
document from the same publisher, counts **once**. Corroboration means independent
corroboration.

## Admissibility

A case's declared binary truth is admissible only if, after the filter:

1. the standard is `vendor-consensus` or stronger, and it is **earned** (enough
   independent sources — see the table);
2. at least one independent source actually **asserts** the declared direction (silence
   and overlap are not support);
3. there is no hard conflict (see below); and
4. any scope dissent is corroborated (see below).

If any condition fails, the effective truth is `contested` or `unadjudicated` and the case
is **excluded** from the error rates and reported in the coverage table instead.

## Disagreement policy

- **Hard conflict** — one independent source asserts *same* and another asserts
  *distinct*. This is `contested`. No authority resolves a direct contradiction, and
  picking a side would defeat the purpose. It is excluded, not averaged.
- **Scope dissent** — a source stops at *overlap* (or records the names as associated
  groups, as MITRE does) while another asserts identity. A scope dissent **downgrades an
  uncorroborated claim to `contested`**: an identity claim that a second independent
  source declines to confirm is not settled. If the binary claim is corroborated by two
  or more independent sources, it stays admissible and the dissent is recorded as a
  caveat.
- **Adjudicator disagreement** — two independent adjudicators reaching different truths
  is recorded as a hard conflict and yields `contested`.

## The strict gate

``run_evaluation.py --adjudicated --strict`` fails if any case claims a binary truth it
did not earn. The corpus can therefore not quietly acquire an ungrounded "same" or
"distinct". The gate is part of CI, together with `--check` against the committed
coverage baseline.

## What remains hard

- **External truth is scarce.** Government/vendor consensus for a *specific* alias pair
  is rarer than it looks; most public alias lists are exactly the weak evidence Cryptonym
  separates out. A corpus that is mostly `contested`/`unadjudicated` is a finding, not a
  failure.
- **Coverage is a result.** The harness reports how much of the corpus met the bar. An
  admissible-case error rate over two cases is honest about being two cases.
- **The adjudicator is still one person.** Independence is enforced between *sources*;
  between *adjudicators* it is not yet, because there is one. That is stated, not hidden.
