"""The method: falsifiable hypotheses, detection strategies, closure and maturity."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from cti_method.contract import HIGH, LOW, MEDIUM, finding, has_high

_DATA = Path(__file__).resolve().parent / "attack.json"
_ATTACK = json.loads(_DATA.read_text(encoding="utf-8"))

#: Hunting Maturity Model (HMM) — the ladder a hunting programme climbs.
HMM_LEVELS: list[dict[str, Any]] = [
    {"level": 0, "name": "Initial", "summary": "Little or no hunting; relies on automated alerting."},
    {"level": 1, "name": "Minimal", "summary": "Ad hoc; basic data collection, no repeatable process."},
    {"level": 2, "name": "Procedural", "summary": "Hunts follow documented procedures from external sources."},
    {"level": 3, "name": "Innovative", "summary": "Analyst-formulated hypotheses; data-driven and threat-informed."},
    {"level": 4, "name": "Leading", "summary": "Successful hunts are automated into detection."},
]

#: The hypothesis has to be stated as *If <condition> then <observable>*. "Verify if X then
#: strengthen Y" is not a hypothesis, and neither is a sentence that merely contains both
#: words somewhere.
_IF_THEN = re.compile(r"^\s*(?:if|when)\b.+?\bthen\b", re.IGNORECASE | re.DOTALL)

#: Telemetry a hypothesis can name. Drawn from ATT&CK data components, not from a wish
#: list: if none of these appears, there is nothing to look at.
_OBSERVABLE_HINTS = (
    "log", "telemetry", "event", "process", "command", "network", "dns", "registry", "file",
    "memory", "flow", "socket", "syscall", "auditd", "sysmon", "wmi", "pipe", "driver",
    "module", "image load", "dll", "script block", "authentication", "auth", "logon",
    "connection", "traffic", "service", "scheduled task", "hash", "user account", "api",
)
_HEDGE_WORDS = ("might", "could", "possibly", "maybe", "perhaps")


def hmm_levels() -> list[dict[str, Any]]:
    """Return the Hunting Maturity Model levels (the ladder this method is judged on)."""
    return list(HMM_LEVELS)


def attack_provenance() -> dict[str, Any]:
    """Where the shipped ATT&CK map came from, so a plan can cite it."""
    return {
        key: _ATTACK[key]
        for key in (
            "source",
            "collection",
            "attack_version",
            "attack_spec_version",
            "collection_modified",
            "note",
        )
    }


def validate_hypothesis(text: str) -> dict[str, Any]:
    """Check a hypothesis is falsifiable and testable.

    High findings: it is not stated as *If … then …*, or it names no observable. A
    hypothesis with no telemetry in it cannot be refuted by looking anywhere, so it is
    refused rather than warned about.
    """
    texto = (text or "").strip()
    lowered = texto.lower()
    findings: list[dict[str, str]] = []

    if not _IF_THEN.match(texto):
        findings.append(
            finding("not-falsifiable", HIGH, "State it as 'If <condition> then <observable>'")
        )
    if not any(hint in lowered for hint in _OBSERVABLE_HINTS):
        findings.append(
            finding(
                "no-observable",
                HIGH,
                "Name the telemetry that would show the condition (a log, an event, a record)",
            )
        )
    if any(word in lowered for word in _HEDGE_WORDS):
        findings.append(finding("hedged", LOW, "Hedging ('might', 'could') weakens a hypothesis"))
    if len(lowered.split()) < 6:
        findings.append(finding("too-vague", MEDIUM, "Hypothesis is too short to be testable"))

    return {"falsifiable": not has_high(findings), "findings": findings}


def detections_for(technique_id: str) -> dict[str, Any]:
    """Return the ATT&CK detection strategies, analytics and data components for a technique.

    ATT&CK v18 (October 2025) deprecated **Data Sources**; the mapping now lives in
    Detection Strategies and Analytics, which reference Data Components. The shipped map
    is a curated subset and says so: an unknown technique is reported as unknown, not
    guessed at.
    """
    key = (technique_id or "").strip().upper()
    entry = _ATTACK["techniques"].get(key)
    if not entry:
        return {
            "technique_id": key or technique_id,
            "known": False,
            "detection_strategies": [],
            "data_components": [],
            "note": (
                "Not in the curated subset (12 techniques). Consult ATT&CK v18+ for the full "
                "Detection Strategy mapping; the subset is curated, not complete."
            ),
            "attack": attack_provenance(),
        }
    components: list[str] = []
    for strategy in entry["detection_strategies"]:
        for analytic in strategy.get("analytics") or []:
            for source in analytic.get("log_sources") or []:
                name = source.get("data_component")
                if name and name not in components:
                    components.append(name)
    return {
        "technique_id": key,
        "known": True,
        "technique": entry["name"],
        "url": entry["url"],
        "subtechniques": entry["subtechniques"],
        "detection_strategies": entry["detection_strategies"],
        "data_components": components,
        "attack": attack_provenance(),
    }


def data_sources_for(technique_id: str) -> dict[str, Any]:
    """Deprecated alias of :func:`detections_for`, kept so old callers keep working.

    ATT&CK deprecated Data Sources in v18; this returns Detection Strategies.
    """
    result = detections_for(technique_id)
    result["deprecated"] = "ATT&CK v18 deprecated Data Sources; this returns detection strategies"
    return result


def assess_hunt_maturity(factors: dict[str, bool]) -> dict[str, Any]:
    """Return the HMM level earned by the given programme factors.

    Factors: ``structured_data``, ``documented_procedures``, ``analyst_hypotheses``,
    ``automated_detection``. Each level requires the previous one.
    """
    level = 0
    if factors.get("structured_data"):
        level = 1
    if level >= 1 and factors.get("documented_procedures"):
        level = 2
    if level >= 2 and factors.get("analyst_hypotheses"):
        level = 3
    if level >= 3 and factors.get("automated_detection"):
        level = 4
    entry = HMM_LEVELS[level]
    return {
        "level": level,
        "name": entry["name"],
        "summary": entry["summary"],
        "gaps": [key for key, value in factors.items() if not value],
    }


def build_hunt_plan(
    question: str,
    hypothesis: str,
    techniques: list[str] | None = None,
    closure: str = "",
    actor: str = "",
    hunt_id: str = "",
    assessment_id: str = "",
) -> dict[str, Any]:
    """Assemble a hunt plan and state whether it is ready to run.

    A plan is *ready* only when the hypothesis is falsifiable, a closure criterion is
    given, and at least one ATT&CK technique anchors it.
    """
    techniques = [item.strip().upper() for item in (techniques or []) if item and item.strip()]
    validation = validate_hypothesis(hypothesis)
    sources = [detections_for(technique) for technique in techniques]

    gaps: list[str] = []
    if not closure:
        gaps.append("no closure criterion: state when the hunt is done, and what 'not found' means")
    if not techniques:
        gaps.append("no ATT&CK technique named: the hunt is not threat-informed")
    if techniques and not any(source["known"] for source in sources):
        gaps.append("no technique is in the curated detection-strategy subset; consult ATT&CK")

    return {
        "id": hunt_id or None,
        "assessment_id": assessment_id or None,
        "question": question,
        "actor": actor or None,
        "hypothesis": hypothesis,
        "validation": validation,
        "techniques": [
            {
                "technique_id": source["technique_id"],
                "known": source["known"],
                "technique": source.get("technique"),
                "detection_strategies": source["detection_strategies"],
                "data_components": source["data_components"],
            }
            for source in sources
        ],
        "closure": closure or None,
        "gaps": gaps,
        "ready": validation["falsifiable"] and bool(closure) and bool(techniques),
    }


def validate_plan(plan: dict[str, Any]) -> dict[str, Any]:
    """Validate a hunt plan document (the JSON form of the plan).

    Same rules as :func:`validate_hypothesis`, plus: a plan with no closure criterion or
    no technique is not ready, and both are high findings — a plan you cannot close is a
    browse.
    """
    findings: list[dict[str, str]] = []
    hypothesis = str(plan.get("hypothesis") or "")
    validation = validate_hypothesis(hypothesis)
    findings.extend(validation["findings"])

    if not str(plan.get("closure") or "").strip():
        findings.append(finding("no-closure", HIGH, "state when the hunt is done, and what 'not found' means"))
    techniques = [str(item).strip().upper() for item in plan.get("techniques") or [] if str(item).strip()]
    if not techniques:
        findings.append(finding("no-technique", HIGH, "name at least one ATT&CK technique"))
    unknown = [item for item in techniques if not detections_for(item)["known"]]
    if unknown and len(unknown) == len(techniques):
        findings.append(
            finding("technique-not-in-subset", MEDIUM, f"{', '.join(unknown)} is not in the curated subset")
        )

    plan_out = build_hunt_plan(
        question=str(plan.get("question") or ""),
        hypothesis=hypothesis,
        techniques=techniques,
        closure=str(plan.get("closure") or ""),
        actor=str(plan.get("actor") or ""),
        hunt_id=str(plan.get("id") or ""),
        assessment_id=str(plan.get("assessment_id") or ""),
    )
    plan_out["validation"] = {"falsifiable": not has_high(findings), "findings": findings}
    plan_out["ready"] = not has_high(findings) and bool(plan_out["closure"]) and bool(techniques)
    return plan_out
