# Method

## The loop

Direction → data → hypothesis → analysis → detection → closure. HuntPlan covers the
front of that loop: turning a question into something testable, and saying when it is done.

## A hypothesis must be falsifiable

- Stated as **If `<condition>` then `<observable>`** — otherwise it cannot be refuted, and
  a hunt that cannot be refuted cannot close.
- It must **name telemetry**: a claim without a data source is a wish.
- **No hedging** ("might", "could"): state what you expect to see.
- **Not too vague**: a hypothesis of a few words is not testable.

## Data sources

Each ATT&CK technique maps to the data sources that would satisfy it. HuntPlan ships a
curated subset (`T1059`, `T1003`, `T1055`, `T1071`, `T1105`, `T1547`, `T1053`, `T1112`,
`T1021`, `T1078`) and **reports absence rather than guessing** — use the ATT&CK data for
the full mapping.

## Closure

A hunt is *ready* only with all three: a falsifiable hypothesis, at least one technique,
and a **closure criterion** that states both the confirmation and the refutation.

## Maturity (HMM)

| Level | Name | Requires |
|---|---|---|
| 0 | Initial | — |
| 1 | Minimal | structured data |
| 2 | Procedural | + documented procedures |
| 3 | Innovative | + analyst-formulated hypotheses |
| 4 | Leading | + automated detection from successful hunts |

Each rung requires the one below it: automation without hypotheses is not maturity.

## What it does not prove

The hypothesis quality checks are heuristics, not a guarantee; the data-source subset is
curated, not exhaustive; and a "ready" plan is a plan, not a finding.
