"""Scoring the reconciliation method: the corpus-specific half.

The arithmetic (confusion, calibration, splits) and the external-truth filter live in
:mod:`cti_method.metrics` and :mod:`cti_method.adjudication`. What stays here is what is
specific to alias work: the positive class is ``same_actor``, and a case is scored by
re-deriving the judgement from its own evidence.
"""

from __future__ import annotations

from cti_method.adjudication import Adjudication, Truth, filter_adjudication
from cti_method.metrics import (
    SPLITS,
    Confusion,
    calibration_table,
    confusion_from_calls,
    probability_calibration,
)

from cryptonym.assess.grading import assess_actor_pair
from cryptonym.model.assessment import Assessment, Hypothesis

POSITIVE = Hypothesis.SAME.value


def _binary_call(verdict: dict) -> tuple[bool | None, str | None, list[str]]:
    """Map the engine's ranking to the corpus's binary question: same actor or not.

    A tie between two *non-same* hypotheses is still a ``False`` call for the binary
    question; it is not an abstention. A tie that includes ``same_actor`` is an abstention:
    the evidence does not decide the question the corpus scores. Resolving any tie with
    ``hypotheses_favoured[0]`` would let the order of the list decide, which is the bug the
    engine's ``tied`` field exists to prevent.
    """
    tied = list(verdict.get("tied") or [])
    if len(tied) > 1:
        abstain = POSITIVE in tied
        return (None if abstain else False), None, tied
    ranking = verdict.get("hypotheses_favoured") or []
    favourite = ranking[0] if ranking else "n/a"
    return favourite == POSITIVE, favourite, tied


def evaluate_cases(cases: list[dict]) -> dict:
    """Run the engine over a labelled corpus and summarise the method.

    Each case carries its authored evidence plus an adjudicated ``truth``. The engine
    re-derives the favourite hypothesis from the evidence; the harness then asks whether
    that favourite agrees with the truth, and at what confidence.
    """
    results: list[dict] = []
    scored: list[dict] = []
    for case in cases:
        assessment = Assessment.from_dict(case)
        verdict = assess_actor_pair(assessment)
        called_same, favourite, tied = _binary_call(verdict)
        truth_same = case["truth"] == POSITIVE
        abstained = called_same is None and len(tied) > 1
        correct = None if called_same is None else called_same == truth_same
        if called_same is not None:
            scored.append(
                {
                    "called_same": called_same,
                    "correct": correct,
                    "truth_same": truth_same,
                    "ceiling": verdict["ceiling"],
                    "probability": verdict["probability"],
                }
            )
        results.append(
            {
                "id": case["id"],
                "truth": case["truth"],
                "favourite": favourite,
                "tied": len(tied) > 1,
                "tied_hypotheses": tied,
                "abstained": abstained,
                "supported": list(verdict.get("supported") or []),
                "unsupported": list(verdict.get("unsupported") or []),
                "called_same": called_same,
                "correct": correct,
                "confidence": verdict["confidence"],
                "ceiling": verdict["ceiling"],
                "probability": verdict["probability"],
                "truth_same": truth_same,
            }
        )
    confusion = confusion_from_calls([(row["called_same"], row["truth_same"]) for row in scored])
    # Calibrate on the ceiling the evidence sets, not on the declared grade: the declared
    # one is prose, and prose does not calibrate.
    calibration = calibration_table([(str(row["ceiling"]), bool(row["correct"])) for row in scored])
    probabilities = probability_calibration([(row["probability"], row["truth_same"]) for row in scored])
    return {
        "results": results,
        "calls": len(scored),
        "abstentions": sum(1 for row in results if row["abstained"]),
        "tied": sum(1 for row in results if row["tied"]),
        "abstained": sum(1 for row in results if row["abstained"]),
        "unsupported": sum(1 for row in results if not row["supported"]),
        "metrics": confusion.as_dict(),
        "calibration": calibration,
        "probability_calibration": probabilities,
    }


def _summarise(cases: list[dict]) -> dict[str, dict]:
    result = evaluate_cases(cases)
    return {
        "metrics": result["metrics"],
        "calls": result["calls"],
        "abstentions": result["abstentions"],
        "tied": result["tied"],
        "abstained": result["abstained"],
        "unsupported": result["unsupported"],
        "calibration": result["calibration"],
        "probability_calibration": result["probability_calibration"],
    }


def evaluate_corpus(document: dict) -> dict:
    """Score a corpus, reported **per split** and overall.

    A method graded on the cases it was tuned against proves nothing, so the development
    and held-out splits are never averaged into one number: the held-out result counts.
    """
    cases = document.get("cases", [])
    splits: dict[str, dict[str, dict]] = {}
    for name in SPLITS:
        subset = [case for case in cases if case.get("split") == name]
        if subset:
            splits[name] = _summarise(subset)
    return {
        "overall": _summarise(cases),
        "splits": splits,
        "results": evaluate_cases(cases)["results"],
    }


def evaluate_adjudicated(document: dict) -> dict:
    """Score an adjudicated corpus: only cases whose truth is *admissible* count.

    Every case is run through the external-truth filter. Cases whose effective truth is
    ``same_actor`` or ``distinct`` enter the confusion matrix; ``contested`` and
    ``unadjudicated`` are reported as **coverage**, never folded into error rates.
    """
    cases = document.get("cases", [])
    calls: list[tuple[bool, bool]] = []
    calibration_records: list[tuple[str, bool]] = []
    probability_records: list[tuple[str | None, bool]] = []
    coverage = {"admissible": 0, "contested": 0, "unadjudicated": 0}
    by_standard: dict[str, int] = {}
    results: list[dict] = []
    tied_count = 0
    abstained_count = 0

    for case in cases:
        adjudication = Adjudication.from_dict(case["adjudication"])
        verdict = filter_adjudication(adjudication)
        engine = assess_actor_pair(Assessment.from_dict(case))
        called_same, favourite, tied = _binary_call(engine)
        abstained = called_same is None and len(tied) > 1
        if len(tied) > 1:
            tied_count += 1
        if abstained:
            abstained_count += 1

        correct: bool | None = None
        if verdict.effective_truth.is_binary:
            coverage["admissible"] += 1
            if called_same is not None:
                calls.append((called_same, verdict.effective_truth is Truth.SAME_ACTOR))
                correct = called_same == (verdict.effective_truth is Truth.SAME_ACTOR)
                calibration_records.append((str(engine["ceiling"]), bool(correct)))
                probability_records.append(
                    (engine["probability"], verdict.effective_truth is Truth.SAME_ACTOR)
                )
        else:
            coverage[verdict.effective_truth.value] = coverage.get(verdict.effective_truth.value, 0) + 1

        if verdict.standard is not None:
            name = verdict.standard.name.lower().replace("_", "-")
            by_standard[name] = by_standard.get(name, 0) + 1

        results.append(
            {
                "id": case["id"],
                "declared_truth": verdict.declared_truth.value,
                "effective_truth": verdict.effective_truth.value,
                "admissible": verdict.admissible,
                "standard": verdict.standard.name.lower().replace("_", "-") if verdict.standard else None,
                "independent_sources": verdict.independent_sources,
                "favourite": favourite,
                "tied": len(tied) > 1,
                "tied_hypotheses": tied,
                "abstained": abstained,
                "supported": list(engine.get("supported") or []),
                "unsupported": list(engine.get("unsupported") or []),
                "called_same": called_same,
                "correct": correct,
                "declared": engine["confidence"],
                "ceiling": engine["ceiling"],
                "reasons": list(verdict.reasons),
            }
        )

    return {
        "metrics": confusion_from_calls(calls).as_dict(),
        "calls": len(calls),
        "abstentions": abstained_count,
        "tied": tied_count,
        "abstained": abstained_count,
        "unsupported": sum(1 for row in results if not row["supported"]),
        "calibration": calibration_table(calibration_records),
        "probability_calibration": probability_calibration(probability_records),
        "coverage": coverage,
        "by_standard": by_standard,
        "results": results,
    }


__all__ = [
    "Confusion",
    "calibration_table",
    "confusion_from_calls",
    "evaluate_adjudicated",
    "evaluate_cases",
    "evaluate_corpus",
]
