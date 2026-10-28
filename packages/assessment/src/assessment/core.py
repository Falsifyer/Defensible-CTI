"""The ledger engine: graded claims, an evidence-derived ceiling and a tamper-evident log.

Every function that needs the shared core imports :mod:`cti_method` directly. The graded
engine is generic, so this package does not import the alias-specific one.

Three rules:

* a claim that declares no confidence is refused (``no-grade``), never defaulted to low;
* a declared confidence **above** what the evidence supports is refused
  (``grade-exceeds-evidence``), with the ceiling and the reasons in the output;
* the ledger is append-only and hash-chained, so a silent edit is detectable.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from importlib import resources
from pathlib import Path
from typing import Any

import cti_method
from cti_method.contract import HIGH, finding, has_high
from cti_method.grading import check_declared, derived_grade
from cti_method.trace import link_requirement

GENESIS = "0" * 64
SCHEMA_VERSION = "1.0"


def _evidence(items: list[dict[str, Any]]) -> list[cti_method.Evidence]:
    return [
        cti_method.Evidence(
            id=item["id"],
            statement=item["statement"],
            source=item["source"],
            type=cti_method.EvidenceType(item["type"]),
            consistency={
                key: cti_method.Consistency(value) for key, value in item.get("consistency", {}).items()
            },
            source_id=item.get("source_id", ""),
            reliability=item.get("reliability", ""),
            direct=bool(item.get("direct", False)),
        )
        for item in items
    ]


def ceiling_for(evidence: list[dict[str, Any]], mode: str = "ach") -> dict[str, Any]:
    """The ceiling the evidence sets on a declared confidence, with its reasons.

    ``mode="claim"`` grades a claim with no competing hypotheses: what matters is whether
    an item bears directly on the claim, not whether it distinguishes actors.
    """
    return derived_grade(_evidence(evidence), mode=mode)


def grade(confidence: str, probability: str | None = None) -> dict[str, Any]:
    """Grade a claim on two independent axes: confidence (always) and probability (estimative)."""
    judgement = cti_method.Judgement(
        confidence=cti_method.parse_confidence(confidence),
        probability=cti_method.parse_probability(probability),
    )
    return {
        "confidence": judgement.confidence.value,
        "probability": judgement.probability.value if judgement.probability is not None else None,
        "two_axis": judgement.is_two_axis(),
        "label": judgement.label(),
    }


def weigh(evidence: list[dict[str, Any]], hypotheses: list[str] | None = None) -> dict[str, Any]:
    """Compare competing hypotheses against a body of evidence (ACH).

    Hypotheses may be any labels, but there must be at least two: ranking one hypothesis
    is not analysis.
    """
    labels = [str(item) for item in hypotheses or [] if str(item).strip()]
    if len(labels) < 2:
        raise ValueError("weighing needs at least two competing hypotheses")
    items = _evidence(evidence)
    matrix = cti_method.consistency_matrix(items, labels)
    return {
        "ranking": cti_method.least_inconsistent(items, labels),
        "inconsistencies": cti_method.inconsistency_counts(items, labels),
        "inconsistency_scores": cti_method.inconsistency_scores(items, labels),
        "discriminating": cti_method.discriminating_evidence(items),
        "consistent_with_everything": cti_method.consistent_with_everything(items),
        "matrix": {
            evidence_id: {label: cell.value for label, cell in row.items()}
            for evidence_id, row in matrix.items()
        },
    }


def filter_truth(adjudication: dict[str, Any]) -> dict[str, Any]:
    """Apply the external-truth filter to an adjudication, returning the effective truth."""
    return cti_method.filter_adjudication(cti_method.Adjudication.from_dict(adjudication)).as_dict()


def assess(document: dict[str, Any], register: dict[str, Any] | None = None) -> dict[str, Any]:
    """Grade a full claim: evidence, competing hypotheses, a two-axis grade and findings.

    A claim is a question, a body of evidence and a declared grade. It carries either one
    hypothesis — the claim itself — or two or more competing ones for an ACH. The evidence
    sets the ceiling; the declaration must not exceed it. If the claim carries an
    ``adjudication``, the external-truth filter decides whether the declared truth is
    admissible.
    """
    evidence_items = _evidence(document.get("evidence") or [])
    sources = list(document.get("sources") or [])
    labels = [str(item) for item in document.get("hypotheses") or [] if str(item).strip()]
    findings: list[dict[str, str]] = []

    if len(labels) == 0:
        findings.append(
            finding(
                "no-claim",
                HIGH,
                "state the claim the evidence supports: one hypothesis, or two competing ones for an ACH",
            )
        )

    mode = "ach" if len(labels) >= 2 else "claim"
    if mode == "ach":
        weighed: dict[str, Any] = weigh(document.get("evidence") or [], labels)
    else:
        weighed = {
            "ranking": [],
            "inconsistencies": {},
            "inconsistency_scores": {},
            "discriminating": [],
            "consistent_with_everything": [],
        }
    favoured = weighed["ranking"][0] if weighed["ranking"] else (labels[0] if labels else None)

    judgement = document.get("judgement") or {}
    declared_raw = judgement.get("confidence")
    declared = cti_method.parse_confidence(declared_raw) if declared_raw else None
    probability = judgement.get("probability")
    parsed_probability = cti_method.parse_probability(probability) if probability else None

    findings.extend(check_declared(declared, evidence_items, sources, favoured, mode=mode))
    derived = derived_grade(evidence_items, sources, favoured, mode=mode)

    if document.get("requirement_id") and register is not None:
        findings.extend(link_requirement(document, register)["findings"])

    verdict: dict[str, Any] = {
        "$schema": "https://github.com/Falsifyer/Defensible-CTI/schemas/judgement.schema.json",
        "schema_version": document.get("schema_version", SCHEMA_VERSION),
        "id": document.get("id"),
        "requirement_id": document.get("requirement_id"),
        "question": document.get("question"),
        "mode": mode,
        "ranking": weighed["ranking"],
        "favoured": favoured,
        "inconsistencies": weighed["inconsistencies"],
        "inconsistency_scores": weighed["inconsistency_scores"],
        "discriminating": weighed["discriminating"],
        "consistent_with_everything": weighed["consistent_with_everything"],
        "grade": {
            "confidence": declared.value if declared is not None else None,
            "probability": parsed_probability.value if parsed_probability is not None else None,
            "two_axis": parsed_probability is not None,
            "label": (
                f"confidence: {declared.value}" if declared is not None else "no grade declared"
            )
            + (f"; probability: {parsed_probability.value}" if parsed_probability is not None else ""),
        },
        "ceiling": derived["ceiling"],
        "grade_supported": declared is not None
        and not has_high(check_declared(declared, evidence_items, sources, favoured, mode=mode)),
        "evidence_profile": derived["profile"],
        "grade_reasons": derived["reasons"],
        "review_by": document.get("review_by"),
        "findings": findings,
    }
    if "adjudication" in document:
        verdict["truth"] = filter_truth(document["adjudication"])
    return verdict


def check_against(verdict: dict[str, Any], previous: dict[str, Any]) -> list[dict[str, str]]:
    """Compare this run with the previous step's judgement.

    The engine is deterministic: the same dossier must produce the same ranking and the
    same ceiling. A disagreement means the dossier changed after the judgement was
    produced, so the chain is broken — a high finding, not a footnote.
    """
    findings: list[dict[str, str]] = []
    previous_ranking = previous.get("hypotheses_favoured") or previous.get("ranking") or []
    if verdict["ranking"] and previous_ranking and verdict["ranking"][0] != previous_ranking[0]:
        findings.append(
            finding(
                "judgement-mismatch",
                HIGH,
                f"this run favours {verdict['ranking'][0]!r} but the supplied judgement favours "
                f"{previous_ranking[0]!r}: the dossier changed after the judgement was produced",
            )
        )
    previous_ceiling = previous.get("ceiling")
    if previous_ceiling and previous_ceiling != verdict["ceiling"]:
        findings.append(
            finding(
                "judgement-mismatch",
                HIGH,
                f"the evidence now supports {verdict['ceiling']!r}; the supplied judgement says {previous_ceiling!r}",
            )
        )
    if not previous_ranking and not previous_ceiling:
        findings.append(
            finding("judgement-unusable", HIGH, "the supplied judgement has no ranking and no ceiling to compare")
        )
    return findings


# ---------------------------------------------------------------- ledger integrity


def _canonical(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical(payload)).hexdigest()


def _entries(path: str | Path) -> list[dict[str, Any]]:
    target = Path(path)
    if not target.exists():
        return []
    entries = []
    for number, line in enumerate(target.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"ledger line {number} is not valid JSON: {exc.msg}") from exc
    return entries


def append_claim(
    path: str | Path,
    claim: dict[str, Any],
    *,
    tool: str = "assessment",
    now: str | None = None,
) -> dict[str, Any]:
    """Append a graded claim to the ledger, chained to the previous entry.

    Each entry records when it was written, what tool wrote it, the hash of the claim, the
    hash of the previous entry and its own hash. A silent edit breaks the chain.
    """
    entries = _entries(path)
    previous = entries[-1]["hash"] if entries else GENESIS
    stamp = now or dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        dt.datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise ValueError("now must be an ISO 8601 UTC timestamp ending in Z") from exc
    entry = {
        "seq": len(entries) + 1,
        "created_at": stamp,
        "tool": tool,
        "claim_id": claim.get("id") or claim.get("assessment_id"),
        "claim_hash": _digest(claim),
        "claim": claim,
        "prev_hash": previous,
    }
    entry["hash"] = _digest(entry)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return {"path": str(target), "seq": entry["seq"], "hash": entry["hash"], "appended": True}


def read_ledger(path: str | Path) -> dict[str, Any]:
    """Read a ledger (JSON Lines) of graded claims."""
    target = Path(path)
    if not target.exists():
        return {"path": str(target), "count": 0, "entries": [], "claims": []}
    entries = _entries(path)
    return {
        "path": str(target),
        "count": len(entries),
        "entries": entries,
        "claims": [entry.get("claim") for entry in entries],
    }


def verify_ledger(path: str | Path) -> dict[str, Any]:
    """Verify the hash chain: sequence, previous hash and own hash, entry by entry."""
    target = Path(path)
    if not target.exists():
        return {"path": str(target), "valid": False, "entries": 0, "broken_at": None,
                "reason": "the ledger does not exist"}
    try:
        entries = _entries(path)
    except ValueError as exc:
        return {"path": str(target), "valid": False, "entries": 0, "broken_at": None, "reason": str(exc)}

    previous = GENESIS
    for index, entry in enumerate(entries, start=1):
        if entry.get("seq") != index:
            return {"path": str(target), "valid": False, "entries": len(entries), "broken_at": index,
                    "reason": f"seq is {entry.get('seq')!r}, expected {index}"}
        if entry.get("prev_hash") != previous:
            return {"path": str(target), "valid": False, "entries": len(entries), "broken_at": index,
                    "reason": "prev_hash does not match the previous entry"}
        body = {key: value for key, value in entry.items() if key != "hash"}
        if entry.get("hash") != _digest(body):
            return {"path": str(target), "valid": False, "entries": len(entries), "broken_at": index,
                    "reason": "the entry hash does not match its content"}
        previous = entry["hash"]
    return {"path": str(target), "valid": True, "entries": len(entries), "broken_at": None, "reason": "chain intact"}


def calibrate(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Score a labelled set of calls: confusion, error rates and calibration by confidence.

    Each case is ``{"id", "called": bool, "truth": bool, "confidence": "high|moderate|low"}``.
    The tool does not decide the truth of a claim; it scores the calls it is given.
    """
    calls = [(bool(case.get("called")), bool(case.get("truth"))) for case in cases]
    records = [(str(case.get("confidence", "")), bool(case.get("called")) == bool(case.get("truth"))) for case in cases]
    return {
        "metrics": cti_method.confusion_from_calls(calls).as_dict(),
        "calibration": cti_method.calibration_table(records),
    }


def method_documentation(section: str = "method") -> dict[str, Any]:
    """Return one of this tool's method documents, from the installed package."""
    try:
        reference = resources.files("assessment").joinpath("docs", f"{section}.md")
    except (ModuleNotFoundError, FileNotFoundError):
        return {"error": "documentation not found in the installed package"}
    if not reference.is_file():
        available = sorted(
            item.name.removesuffix(".md")
            for item in resources.files("assessment").joinpath("docs").iterdir()
            if item.name.endswith(".md")
        )
        return {"error": f"unknown section {section!r}", "available": available}
    return {"section": section, "content": reference.read_text(encoding="utf-8")}
