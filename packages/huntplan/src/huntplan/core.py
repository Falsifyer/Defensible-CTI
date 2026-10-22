"""The method: falsifiable hypotheses, ATT&CK data sources, closure and maturity."""

from __future__ import annotations

from typing import Any

HIGH, MEDIUM, LOW = "high", "medium", "low"

#: Hunting Maturity Model (HMM) — the ladder a hunting programme climbs.
HMM_LEVELS: list[dict[str, Any]] = [
    {"level": 0, "name": "Initial", "summary": "Little or no hunting; relies on automated alerting."},
    {"level": 1, "name": "Minimal", "summary": "Ad hoc; basic data collection, no repeatable process."},
    {"level": 2, "name": "Procedural", "summary": "Hunts follow documented procedures from external sources."},
    {"level": 3, "name": "Innovative", "summary": "Analyst-formulated hypotheses; data-driven and threat-informed."},
    {"level": 4, "name": "Leading", "summary": "Successful hunts are automated into detection."},
]

#: Curated ATT&CK technique -> data-source subset. Deliberately small: for the full
#: mapping, consult the ATT&CK data itself (see the ATT&CK MCP). Absence is reported, not
#: guessed at.
DATA_SOURCES: dict[str, dict[str, Any]] = {
    "T1059": {
        "technique": "Command and Scripting Interpreter",
        "sources": ["Process creation (command line)", "Script block logging", "Module load"],
    },
    "T1003": {
        "technique": "OS Credential Dumping",
        "sources": ["Process access (LSASS)", "Process creation", "File access"],
    },
    "T1055": {
        "technique": "Process Injection",
        "sources": ["Process access", "Memory allocation", "API calls"],
    },
    "T1071": {
        "technique": "Application Layer Protocol",
        "sources": ["Network traffic (flow)", "Network traffic (content)", "Process creation"],
    },
    "T1105": {
        "technique": "Ingress Tool Transfer",
        "sources": ["File creation", "Network traffic", "Process creation"],
    },
    "T1547": {
        "technique": "Boot or Logon Autostart Execution",
        "sources": ["Registry", "File creation", "Service creation"],
    },
    "T1053": {
        "technique": "Scheduled Task/Job",
        "sources": ["Scheduled task creation", "Process creation", "Command line"],
    },
    "T1112": {
        "technique": "Modify Registry",
        "sources": ["Registry", "Process creation"],
    },
    "T1021": {
        "technique": "Remote Services",
        "sources": ["Authentication logs", "Network traffic", "Process creation"],
    },
    "T1078": {
        "technique": "Valid Accounts",
        "sources": ["Authentication logs", "Process creation", "Network traffic"],
    },
}

_DATA_SOURCE_HINTS = (
    "log", "telemetry", "process", "network", "dns", "registry", "event",
    "sysmon", "authentication", "file", "memory", "command", "flow",
)
_HEDGE_WORDS = ("might", "could", "possibly", "maybe", "perhaps")


def _finding(code: str, severity: str, message: str) -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


def hmm_levels() -> list[dict[str, Any]]:
    """Return the Hunting Maturity Model levels (the ladder this method is judged on)."""
    return list(HMM_LEVELS)


def validate_hypothesis(text: str) -> dict[str, Any]:
    """Check a hypothesis is falsifiable and testable.

    Flags a hypothesis that is not stated as *If … then …*, one that names no telemetry,
    one that is hedged, and one that is too vague to be worth running.
    """
    lowered = (text or "").lower()
    findings: list[dict[str, str]] = []
    if "if" not in lowered or "then" not in lowered:
        findings.append(
            _finding("not-falsifiable", HIGH, "State it as 'If <condition> then <observable>'")
        )
    if not any(hint in lowered for hint in _DATA_SOURCE_HINTS):
        findings.append(_finding("no-data-source", MEDIUM, "Name the telemetry that would satisfy the hypothesis"))
    if any(word in lowered for word in _HEDGE_WORDS):
        findings.append(_finding("hedged", LOW, "Hedging ('might', 'could') weakens a hypothesis"))
    if len(lowered.split()) < 6:
        findings.append(_finding("too-vague", MEDIUM, "Hypothesis is too short to be testable"))
    return {"falsifiable": not any(f["severity"] == HIGH for f in findings), "findings": findings}


def data_sources_for(technique_id: str) -> dict[str, Any]:
    """Return the required data sources for a technique from the curated subset."""
    entry = DATA_SOURCES.get((technique_id or "").upper())
    if not entry:
        return {
            "technique_id": technique_id,
            "known": False,
            "sources": [],
            "note": "Not in the curated subset; consult the ATT&CK MCP for the full data-source mapping.",
        }
    return {"technique_id": technique_id.upper(), "known": True, **entry}


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
) -> dict[str, Any]:
    """Assemble a hunt plan and state whether it is ready to run.

    A plan is *ready* only when the hypothesis is falsifiable, a closure criterion is
    given, and at least one ATT&CK technique anchors it.
    """
    techniques = techniques or []
    validation = validate_hypothesis(hypothesis)
    sources = [data_sources_for(technique) for technique in techniques]

    gaps: list[str] = []
    if not closure:
        gaps.append("no closure criterion: state when the hunt is done, and what 'not found' means")
    if not techniques:
        gaps.append("no ATT&CK technique named: the hunt is not threat-informed")
    if techniques and not any(source["known"] for source in sources):
        gaps.append("no technique is in the curated data-source subset; consult the ATT&CK MCP")

    return {
        "question": question,
        "actor": actor or None,
        "hypothesis": hypothesis,
        "validation": validation,
        "techniques": [
            {"technique_id": source["technique_id"], "known": source["known"], "sources": source["sources"]}
            for source in sources
        ],
        "closure": closure or None,
        "gaps": gaps,
        "ready": validation["falsifiable"] and bool(closure) and bool(techniques),
    }
