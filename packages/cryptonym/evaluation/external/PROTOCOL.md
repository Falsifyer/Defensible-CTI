# External corpus protocol

**Status:** scaffold for phases 1–2. There are **no real cases** in this directory yet.
This document is the contract a case must satisfy before it becomes evidence about the
method. It is deliberately separate from `../adjudicated/`, whose seed cases are
illustrative and authored inside the project.

The unit is one **binary identity question**: *are designation A and designation B the same
actor?* The engine is not asked who an actor is. It is asked whether the evidence it is
given supports `same_actor`, `distinct_but_overlapping`, or `brokered_shared_access`, and
at what confidence.

## 1. Roles and independence

| Role | Who | Cannot be |
|---|---|---|
| Case author | assembles the evidence and sources | the sole adjudicator of their own case |
| Adjudicator 1 | independently decides the truth from the sources | the case author |
| Adjudicator 2 | independently decides the truth from the sources | the case author, or the same person as 1 |
| Custodian | freezes the split and runs the engine once | an adjudicator of the held-out cases |
| Reviewer | checks provenance and the protocol | — |

A **binary truth requires two independent adjudicators**. Each records a truth and a
standard before seeing the other's decision. If they disagree, the case is `contested`;
the custodian does not pick a winner.

The **author may not be the sole adjudicator**. The existing seed corpus is an
author-assertion corpus and is labelled as such; it is not eligible for the external
figures.

## 2. Blindness

Adjudicators receive a packet containing:

- the question and the two designations;
- the evidence items and their sources;
- the source URLs and, where captured, the snapshot SHA-256.

They do **not** receive:

- the engine's ranking, ceiling, `favoured`, `tied`, `supported` or findings;
- the `judgement` block the analyst declared;
- the other adjudicator's decision.

The engine receives the frozen case **without** the `adjudication` block. The custodian
removes `adjudication` and `judgement` before running; the truth is joined back only after
the output is written. This is what makes the comparison a test rather than a
self-fulfilling exercise.

## 3. Source independence

Two sources are one voice if they share a publisher or if one derives from the other.
Record this structurally, not in prose:

- `publisher` — the organisation that made the claim;
- `url` — the document actually read;
- `category` — `government`, `vendor`, `community` or `osint`;
- `kind` — `asserts-same`, `asserts-distinct`, `overlap` or `silent`;
- `derived_from` — the publisher(s) this document repeats;
- `accessed_at` and `snapshot_sha256` — when the document was read and the hash of the
  bytes seen.

A source that derives from another source present counts once. A second document from the
same publisher counts once. `overlap` is **not** support for a binary truth; `silent` is
not evidence of the opposite.

For `infrastructure`, `code` and `operator` evidence, record a structured `artifact`
(`kind` + `value`: hash, domain, URL, IP, certificate, pattern or handle) and where it was
verified. Prose alone is not enough for an identity call.

For each binary case, at least **two independent sources must actually assert the declared
direction**, or the truth is `contested`/`unadjudicated`. See
[`../../src/cryptonym/docs/adjudication.md`](../../src/cryptonym/docs/adjudication.md) for
the executable standard.

## 4. Adjudication vocabulary

| Truth | Meaning | Enters error rates? |
|---|---|---|
| `same_actor` | two designations name the same actor | yes |
| `distinct` | they do not | yes |
| `contested` | independent sources genuinely disagree, or scope is unresolved | no; coverage |
| `unadjudicated` | too thin, or no independent source asserts a stance | no; coverage |

A binary truth also records a `standard`:

| Standard | Minimum independent sources |
|---|---|
| `author-assertion` | never admissible |
| `single-source` | never admissible |
| `vendor-consensus` | 2 |
| `government-statement` | 1 government **+ 1 corroborating** |
| `independent-corroboration` | 2 |

A government name-list alone does not settle a disputed alias. If a source stops at
`overlap` while another asserts identity, the case is `contested` unless the identity claim
is corroborated by two independent sources; the dissent is recorded as a caveat.

## 5. Case selection

Include a case only when:

- the question is a genuine binary identity question, not a request to name an actor;
- the evidence can be shown to the engine without the truth;
- the sources are public or shareable under their terms;
- the case is not a duplicate of another case (same designations, same evidence);
- the author is not the only person who has read the sources.

Exclude or mark `unadjudicated` when the only source is the author, a single vendor
repeating itself, or a name-list that merely lists the two names without asserting identity.

The corpus is allowed to be mostly `contested`/`unadjudicated`. That is a finding about
public alias evidence, not a failure to be hidden.

## 6. Split and freeze

Every case is assigned to exactly one split, **before** the first engine run:

- `development` — may be inspected while building the method;
- `held-out` — frozen; the custodian runs it once and publishes the result.

The split is committed with the case. Moving a case from held-out to development after a
run is a protocol violation. The held-out result is the one that counts; development is
reported separately and is never averaged into it.

## 7. Pre-registration

Before the first run, commit:

- `protocol_version`;
- the metric names and denominators: `calls`, `abstentions`, `unsupported`,
  `false_merge_rate`, `false_split_rate`, Brier score;
- the sample size and split;
- the decision rule for `contested` and `unadjudicated` (excluded from error rates,
  reported as coverage);
- the exact command used to run the evaluation.

No metric may be added, removed or redefined after seeing the result without publishing the
change as a new protocol version and re-running on a fresh held-out set.

## 8. Metrics and reporting

The harness prints and the report must include:

- **calls** — cases that produce a binary call;
- **abstentions** — ties that include `same_actor` (no binary call);
- **unsupported** — cases with no diagnostic support;
- **false_merge_rate** — distinct pairs called same / distinct pairs;
- **false_split_rate** — same pairs called distinct / same pairs;
- **Brier score** — only over estimative calls, with the number of calls;
- **coverage** — admissible / contested / unadjudicated;
- **per-split** results, never only an overall number.

A headline "accuracy" without the denominator is not published. `23 calls, 1 abstention,
1 unsupported` is a result; `100 %` is not.

## 9. Provenance, law and ethics

- Prefer public sources; record the exact URL and access date.
- Capture a snapshot hash where the licence permits; do not republish paywalled text.
- Do not include personal data that is not necessary to the identity question.
- Do not publish a claim of criminality or attribution that the sources do not support;
  the corpus is about identity, not about naming a culprit.
- Respect the source's terms of use and any TLP/handling caveat.
- Keep the source graph (`derived_from`) so a reader can test independence.

## 10. Workflow

1. Author fills `case.template.json` and collects sources.
2. Custodian checks the case against `schema.json` and the independence rules.
3. Two adjudicators receive the blind packet and record truth/standard separately.
4. Custodian reconciles: agreement → binary truth; disagreement → `contested`.
5. Custodian assigns/confirms the split and freezes the case.
6. Engine runs on the frozen evidence without `adjudication`/`judgement`.
7. Custodian joins truth to output, runs `--adjudicated --check --strict`, and writes
   `expected.json`.
8. Report publishes calls, abstentions, unsupported, errors, coverage, disagreements and
   limitations.

## 11. Acceptance checklist for phases 1–2

- [ ] Two named adjudicators have accepted this protocol in writing before seeing cases.
- [ ] `schema.json` validates (`jsonschema.Draft202012Validator.check_schema`).
- [ ] `case.template.json` validates against `schema.json` and is clearly marked as a
      template, not a case.
- [ ] Every binary case has two independent adjudicators and two independent sources, or
      is recorded as `contested`.
- [ ] The split is committed before the first run.
- [ ] The metric list and denominators are committed before the first run.
- [ ] No real case is added to this repository until the author can show the source graph.

Until those boxes are ticked, this directory is **scaffolding**, not a corpus.
