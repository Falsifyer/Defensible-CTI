# Method

## The loop

Direction → data → hypothesis → analysis → detection → closure. HuntPlan covers the
front of that loop: turning a question into something testable, and saying when it is done.

## A hypothesis must be falsifiable

- Stated as **If `<condition>` then `<observable>`** — otherwise it cannot be refuted, and
  a hunt that cannot be refuted cannot close.
- It must **name telemetry**: a claim without an observable is a wish. Naming no log, event
  or record is a high finding (`no-observable`).
- **No hedging** ("might", "could"): state what you expect to see.
- **Not too vague**: a hypothesis of a few words is not testable.

## Detection strategies (ATT&CK v18+)

ATT&CK **deprecated Data Sources in v18 (October 2025)** and replaced the detection mapping
with **Detection Strategies** and **Analytics**, which reference **Data Components**.

`src/huntplan/attack.json` is generated from the Enterprise ATT&CK STIX collection
(currently 20.0, modified 2026-10-13) by `scripts/build_attack_map.py`, and committed with
its provenance (collection version, modification date and SHA-256). It carries a curated
subset of twelve techniques (`T1059`, `T1003`, `T1055`, `T1071`, `T1105`, `T1547`, `T1053`,
`T1112`, `T1021`, `T1078`, `T1566`, `T1047`) with their strategies, analytics, platforms and
log channels. Unknown techniques are **reported as unknown**, never guessed at; for the full
mapping, use the ATT&CK data itself.

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

The hypothesis checks are heuristics, not a guarantee (they check structure and the presence
of an observable, not whether the observable is the right one); the detection-strategy subset
is curated, not exhaustive; and a "ready" plan is a plan, not a finding.
