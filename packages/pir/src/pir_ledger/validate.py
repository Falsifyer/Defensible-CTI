"""Validacion de un registro de requisitos de inteligencia.

La regla que sostiene todo: **una PIR que no nombra la decision que informa no es una
PIR, es un tema de interes**. El validador la rechaza, igual que `huntplan` rechaza una
hipotesis que no se puede refutar.
"""

from __future__ import annotations

import datetime as dt
import re
from typing import Any

from cti_method.contract import HIGH, MEDIUM, finding, has_high, severity_counts

SCHEMA_VERSION = "1.0"

# Escala Admiralty: fiabilidad de la fuente (A-F) y credibilidad de la informacion (1-6).
ADMIRALTY = re.compile(r"^[A-F][1-6]$")
PRIORIDADES = ("high", "medium", "low")


def _fecha(valor: Any) -> dt.date | None:
    if not isinstance(valor, str):
        return None
    try:
        return dt.date.fromisoformat(valor)
    except ValueError:
        return None


def validate(documento: dict[str, Any], hoy: dt.date | None = None) -> dict[str, Any]:
    """Devuelve los hallazgos y si el registro es valido.

    Un hallazgo de severidad `high` invalida el registro; los `medium` avisan.
    """
    hoy = hoy or dt.date.today()
    if not isinstance(documento, dict):
        return {
            "valid": False,
            "findings": [finding("not-an-object", HIGH, "the register is not a JSON object")],
            "requirements": 0,
            "high": 1,
            "medium": 0,
            "ids": [],
            "register_id": None,
        }

    requisitos = documento.get("requirements")
    hallazgos: list[dict[str, str]] = []
    ids: list[str] = []

    if not isinstance(requisitos, list) or not requisitos:
        hallazgos.append(finding("no-requirements", HIGH, "the register has no requirements"))
        return {
            "valid": False,
            "findings": hallazgos,
            "requirements": 0,
            "high": 1,
            "medium": 0,
            "ids": [],
            "register_id": documento.get("id"),
        }

    vistos: set[str] = set()
    for i, pir in enumerate(requisitos):
        if not isinstance(pir, dict):
            hallazgos.append(finding("malformed", HIGH, "the requirement is not an object", where=f"requirements[{i}]"))
            continue
        donde = str(pir.get("id") or f"requirements[{i}]")
        if donde in vistos:
            hallazgos.append(finding("duplicate-id", HIGH, "duplicate identifier", where=donde))
        else:
            ids.append(donde)
        vistos.add(donde)

        pregunta = (pir.get("question") or "").strip()
        if not pregunta:
            hallazgos.append(finding("no-question", HIGH, "no question", where=donde))
        elif not pregunta.endswith("?"):
            hallazgos.append(
                finding(
                    "not-a-question",
                    MEDIUM,
                    "the question does not end in '?': a statement is not answerable",
                    where=donde,
                )
            )

        # La regla central: sin decision, no es una PIR.
        if not (pir.get("decision") or "").strip():
            hallazgos.append(
                finding(
                    "no-decision",
                    HIGH,
                    "does not name the decision it informs: that is a topic of interest, not a PIR",
                    where=donde,
                )
            )
        if not (pir.get("consumer") or "").strip():
            hallazgos.append(finding("no-consumer", HIGH, "does not say who takes that decision", where=donde))
        if pir.get("priority") not in PRIORIDADES:
            hallazgos.append(
                finding(
                    "bad-priority",
                    MEDIUM,
                    f"priority {pir.get('priority')!r}: expected one of {', '.join(PRIORIDADES)}",
                    where=donde,
                )
            )

        limite = _fecha(pir.get("deadline"))
        if pir.get("deadline") and limite is None:
            hallazgos.append(finding("bad-deadline", MEDIUM, "not an ISO date (YYYY-MM-DD)", where=donde))
        if limite and limite < hoy and pir.get("status") != "answered":
            hallazgos.append(
                finding(
                    "stale",
                    MEDIUM,
                    f"overdue since {limite.isoformat()} and unanswered: retire or renew it",
                    where=donde,
                )
            )

        eei = pir.get("eei")
        if not isinstance(eei, list) or not eei:
            hallazgos.append(finding("no-eei", HIGH, "no EEI: there is nothing to collect", where=donde))
            continue
        for j, elemento in enumerate(eei):
            punto = f"{donde}/eei[{j}]"
            if not isinstance(elemento, dict) or not (elemento.get("question") or "").strip():
                hallazgos.append(finding("eei-no-question", HIGH, "EEI without a question", where=punto))
                continue
            indicadores = elemento.get("indicators")
            if not isinstance(indicadores, list) or not indicadores:
                hallazgos.append(
                    finding(
                        "eei-no-indicator",
                        MEDIUM,
                        "EEI with no indicator: there is no way to know when it is answered",
                        where=punto,
                    )
                )
                continue
            for indicador in indicadores:
                valor = (indicador or {}).get("value") if isinstance(indicador, dict) else None
                fuente = (indicador or {}).get("source") if isinstance(indicador, dict) else None
                if not valor:
                    hallazgos.append(finding("indicator-no-value", HIGH, "indicator without a value", where=punto))
                if fuente is None:
                    hallazgos.append(
                        finding(
                            "indicator-ungraded",
                            HIGH,
                            f"indicator {valor!r} is ungraded: the source goes as A-F + 1-6",
                            where=punto,
                        )
                    )
                elif not ADMIRALTY.match(str(fuente)):
                    hallazgos.append(
                        finding(
                            "bad-admiralty",
                            MEDIUM,
                            f"grade {fuente!r} is outside the Admiralty scale (A2, B3, ...)",
                            where=punto,
                        )
                    )

    counts = severity_counts(hallazgos)
    return {
        "valid": not has_high(hallazgos),
        "findings": hallazgos,
        "requirements": len(requisitos),
        "high": counts[HIGH],
        "medium": counts[MEDIUM],
        "ids": ids,
        "register_id": documento.get("id"),
        "schema_version": documento.get("schema_version", SCHEMA_VERSION),
    }
