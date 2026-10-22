"""Validation of a register of intelligence requirements.

The rule that holds everything up: **a PIR that does not name the decision it informs is
not a PIR, it is a topic of interest**. The validator rejects it, just as `huntplan`
rejects a hypothesis that cannot be refuted.
"""

from __future__ import annotations

import datetime as dt
import re
from typing import Any

from cti_method.contract import HIGH, MEDIUM, finding, has_high, severity_counts

SCHEMA_VERSION = "1.0"

# Admiralty scale: source reliability (A-F) and information credibility (1-6).
ADMIRALTY = re.compile(r"^[A-F][1-6]$")
PRIORITIES = ("high", "medium", "low")


def _date(value: Any) -> dt.date | None:
    if not isinstance(value, str):
        return None
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        return None


def validate(document: dict[str, Any], today: dt.date | None = None) -> dict[str, Any]:
    """Return the findings and whether the register is valid.

    A `high` finding invalidates the register; `medium` findings are warnings.
    """
    today = today or dt.date.today()
    if not isinstance(document, dict):
        return {
            "valid": False,
            "findings": [finding("not-an-object", HIGH, "the register is not a JSON object")],
            "requirements": 0,
            "high": 1,
            "medium": 0,
            "ids": [],
            "register_id": None,
        }

    requirements = document.get("requirements")
    findings: list[dict[str, str]] = []
    ids: list[str] = []

    if not isinstance(requirements, list) or not requirements:
        findings.append(finding("no-requirements", HIGH, "the register has no requirements"))
        return {
            "valid": False,
            "findings": findings,
            "requirements": 0,
            "high": 1,
            "medium": 0,
            "ids": [],
            "register_id": document.get("id"),
        }

    seen: set[str] = set()
    for index, pir in enumerate(requirements):
        if not isinstance(pir, dict):
            findings.append(
                finding("malformed", HIGH, "the requirement is not an object", where=f"requirements[{index}]")
            )
            continue
        where = str(pir.get("id") or f"requirements[{index}]")
        if where in seen:
            findings.append(finding("duplicate-id", HIGH, "duplicate identifier", where=where))
        else:
            ids.append(where)
        seen.add(where)

        question = (pir.get("question") or "").strip()
        if not question:
            findings.append(finding("no-question", HIGH, "no question", where=where))
        elif not question.endswith("?"):
            findings.append(
                finding(
                    "not-a-question",
                    MEDIUM,
                    "the question does not end in '?': a statement is not answerable",
                    where=where,
                )
            )

        # The central rule: no decision, no PIR.
        if not (pir.get("decision") or "").strip():
            findings.append(
                finding(
                    "no-decision",
                    HIGH,
                    "does not name the decision it informs: that is a topic of interest, not a PIR",
                    where=where,
                )
            )
        if not (pir.get("consumer") or "").strip():
            findings.append(finding("no-consumer", HIGH, "does not say who takes that decision", where=where))
        if pir.get("priority") not in PRIORITIES:
            findings.append(
                finding(
                    "bad-priority",
                    MEDIUM,
                    f"priority {pir.get('priority')!r}: expected one of {', '.join(PRIORITIES)}",
                    where=where,
                )
            )

        deadline = _date(pir.get("deadline"))
        if pir.get("deadline") and deadline is None:
            findings.append(finding("bad-deadline", MEDIUM, "not an ISO date (YYYY-MM-DD)", where=where))
        if deadline and deadline < today and pir.get("status") != "answered":
            findings.append(
                finding(
                    "stale",
                    MEDIUM,
                    f"overdue since {deadline.isoformat()} and unanswered: retire or renew it",
                    where=where,
                )
            )

        eei = pir.get("eei")
        if not isinstance(eei, list) or not eei:
            findings.append(finding("no-eei", HIGH, "no EEI: there is nothing to collect", where=where))
            continue
        for position, element in enumerate(eei):
            pointer = f"{where}/eei[{position}]"
            if not isinstance(element, dict) or not (element.get("question") or "").strip():
                findings.append(finding("eei-no-question", HIGH, "EEI without a question", where=pointer))
                continue
            indicators = element.get("indicators")
            if not isinstance(indicators, list) or not indicators:
                findings.append(
                    finding(
                        "eei-no-indicator",
                        MEDIUM,
                        "EEI with no indicator: there is no way to know when it is answered",
                        where=pointer,
                    )
                )
                continue
            for indicator in indicators:
                value = (indicator or {}).get("value") if isinstance(indicator, dict) else None
                source = (indicator or {}).get("source") if isinstance(indicator, dict) else None
                if not value:
                    findings.append(finding("indicator-no-value", HIGH, "indicator without a value", where=pointer))
                if source is None:
                    findings.append(
                        finding(
                            "indicator-ungraded",
                            HIGH,
                            f"indicator {value!r} is ungraded: the source goes as A-F + 1-6",
                            where=pointer,
                        )
                    )
                elif not ADMIRALTY.match(str(source)):
                    findings.append(
                        finding(
                            "bad-admiralty",
                            MEDIUM,
                            f"grade {source!r} is outside the Admiralty scale (A2, B3, ...)",
                            where=pointer,
                        )
                    )

    counts = severity_counts(findings)
    return {
        "valid": not has_high(findings),
        "findings": findings,
        "requirements": len(requirements),
        "high": counts[HIGH],
        "medium": counts[MEDIUM],
        "ids": ids,
        "register_id": document.get("id"),
        "schema_version": document.get("schema_version", SCHEMA_VERSION),
    }
