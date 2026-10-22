"""The ledger engine.

Every function that needs the shared core imports it lazily, so the package can be
imported (and its offline parts tested) even when the core is not installed — but the
graded paths fail loudly if it is missing.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _method() -> Any:
    """Import the shared core lazily, with a clear error if it is missing."""
    try:
        import cryptonym.method as method
    except ImportError as exc:  # pragma: no cover - exercised by the missing-core test
        raise RuntimeError("the shared core is required: pip install cryptonym (see docs/method.md)") from exc
    return method


def grade(confidence: str, probability: str | None = None) -> dict[str, Any]:
    """Grade a claim on two independent axes: confidence (always) and probability (estimative only)."""
    method = _method()
    judgement = method.Judgement(
        confidence=method.parse_confidence(confidence),
        probability=method.parse_probability(probability),
    )
    return {
        "confidence": judgement.confidence.value,
        "probability": judgement.probability.value if judgement.probability is not None else None,
        "two_axis": judgement.is_two_axis(),
        "label": judgement.label(),
    }


def weigh(evidence: list[dict[str, Any]], hypotheses: list[str] | None = None) -> dict[str, Any]:
    """Compare competing hypotheses against a body of evidence (ACH).

    Hypotheses may be any labels — the engine is not tied to a taxonomy. Returns the
    ranking by least-inconsistent evidence, the per-hypothesis inconsistencies, the
    consistency matrix, and the evidence that discriminates.
    """
    method = _method()
    items = [
        method.Evidence(
            id=item["id"],
            statement=item["statement"],
            source=item["source"],
            type=method.EvidenceType(item["type"]),
            consistency={key: method.Consistency(value) for key, value in item.get("consistency", {}).items()},
        )
        for item in evidence
    ]
    labels = hypotheses or None
    matrix = method.consistency_matrix(items, labels)
    return {
        "ranking": method.least_inconsistent(items, labels),
        "inconsistencies": method.inconsistency_counts(items, labels),
        "discriminating": method.discriminating_evidence(items),
        "consistent_with_everything": method.consistent_with_everything(items),
        "matrix": {
            evidence_id: {label: cell.value for label, cell in row.items()}
            for evidence_id, row in matrix.items()
        },
    }


def filter_truth(adjudication: dict[str, Any]) -> dict[str, Any]:
    """Apply the external-truth filter to an adjudication, returning the effective truth."""
    method = _method()
    return method.filter_adjudication(method.Adjudication.from_dict(adjudication)).as_dict()


def assess(document: dict[str, Any]) -> dict[str, Any]:
    """Grade a full claim: evidence + hypotheses + a two-axis grade, with optional adjudication.

    A claim is a question, a body of evidence, competing hypotheses and a grade. If it
    carries an ``adjudication``, the external-truth filter decides whether the declared
    truth is admissible.
    """
    weighed = weigh(document.get("evidence", []), document.get("hypotheses"))
    judgement = document.get("judgement", {})
    verdict: dict[str, Any] = {
        "question": document.get("question"),
        "ranking": weighed["ranking"],
        "inconsistencies": weighed["inconsistencies"],
        "discriminating": weighed["discriminating"],
        "consistent_with_everything": weighed["consistent_with_everything"],
        "grade": grade(judgement.get("confidence", "low"), judgement.get("probability")),
    }
    if "adjudication" in document:
        verdict["truth"] = filter_truth(document["adjudication"])
    return verdict


def append_claim(path: str, claim: dict[str, Any]) -> dict[str, Any]:
    """Append a graded claim to a ledger (JSON Lines), creating it if needed."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(claim, ensure_ascii=False) + "\n")
    return {"path": str(target), "appended": True}


def read_ledger(path: str) -> dict[str, Any]:
    """Read a ledger (JSON Lines) of graded claims."""
    target = Path(path)
    if not target.exists():
        return {"path": str(target), "count": 0, "claims": []}
    claims = [json.loads(line) for line in target.read_text(encoding="utf-8").splitlines() if line.strip()]
    return {"path": str(target), "count": len(claims), "claims": claims}


def calibrate(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Score a labelled set of claims: false-merge rate, false-split rate and calibration."""
    method = _method()
    return method.evaluate_cases(cases)


def method_documentation(section: str = "method") -> dict[str, Any]:
    """Return one of this tool's method documents."""
    path = Path(__file__).resolve().parents[2] / "docs" / f"{section}.md"
    if not path.exists():
        return {"error": "documentation not found; install assessment-mcp from its repository (editable)"}
    return {"section": section, "content": path.read_text(encoding="utf-8")}
