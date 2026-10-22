"""Validacion de un registro de requisitos de inteligencia.

La regla que sostiene todo: **una PIR que no nombra la decision que informa no es una
PIR, es un tema de interes**. El validador la rechaza, igual que `huntplan` rechaza una
hipotesis que no se puede refutar.
"""

from __future__ import annotations

import datetime as dt
import re
from typing import Any

# Escala Admiralty: fiabilidad de la fuente (A-F) y credibilidad de la informacion (1-6).
ADMIRALTY = re.compile(r"^[A-F][1-6]$")
PRIORIDADES = ("high", "medium", "low")


def _hallazgo(codigo: str, severidad: str, donde: str, mensaje: str) -> dict[str, str]:
    return {"code": codigo, "severity": severidad, "where": donde, "message": mensaje}


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
    requisitos = documento.get("requirements")
    hallazgos: list[dict[str, str]] = []

    if not isinstance(requisitos, list) or not requisitos:
        hallazgos.append(_hallazgo("no-requirements", "high", "-", "el registro no tiene requisitos"))
        return {"valid": False, "findings": hallazgos, "requirements": 0}

    vistos: set[str] = set()
    for i, pir in enumerate(requisitos):
        donde = pir.get("id") if isinstance(pir, dict) and pir.get("id") else f"requirements[{i}]"
        if not isinstance(pir, dict):
            hallazgos.append(_hallazgo("malformed", "high", donde, "el requisito no es un objeto"))
            continue
        if donde in vistos:
            hallazgos.append(_hallazgo("duplicate-id", "high", donde, "identificador repetido"))
        vistos.add(donde)

        pregunta = (pir.get("question") or "").strip()
        if not pregunta:
            hallazgos.append(_hallazgo("no-question", "high", donde, "no hay pregunta"))
        elif not pregunta.endswith("?"):
            hallazgos.append(_hallazgo(
                "not-a-question", "medium", donde,
                "la pregunta no termina en '?': un enunciado no es contestable"))

        # La regla central: sin decision, no es una PIR.
        if not (pir.get("decision") or "").strip():
            hallazgos.append(_hallazgo(
                "no-decision", "high", donde,
                "no nombra la decision que informa: es un tema de interes, no una PIR"))
        if not (pir.get("consumer") or "").strip():
            hallazgos.append(_hallazgo(
                "no-consumer", "high", donde, "no dice quien toma esa decision"))
        if pir.get("priority") not in PRIORIDADES:
            hallazgos.append(_hallazgo(
                "bad-priority", "medium", donde,
                f"prioridad {pir.get('priority')!r}: se espera una de {', '.join(PRIORIDADES)}"))

        limite = _fecha(pir.get("deadline"))
        if pir.get("deadline") and limite is None:
            hallazgos.append(_hallazgo("bad-deadline", "medium", donde, "fecha no ISO (AAAA-MM-DD)"))
        if limite and limite < hoy and pir.get("status") != "answered":
            hallazgos.append(_hallazgo(
                "stale", "medium", donde,
                f"vencida el {limite.isoformat()} y sin responder: se retira o se renueva"))

        eei = pir.get("eei")
        if not isinstance(eei, list) or not eei:
            hallazgos.append(_hallazgo(
                "no-eei", "high", donde, "no tiene EEI: no hay nada que recolectar"))
            continue
        for j, elemento in enumerate(eei):
            punto = f"{donde}/eei[{j}]"
            if not isinstance(elemento, dict) or not (elemento.get("question") or "").strip():
                hallazgos.append(_hallazgo("eei-no-question", "high", punto, "EEI sin pregunta"))
                continue
            indicadores = elemento.get("indicators")
            if not isinstance(indicadores, list) or not indicadores:
                hallazgos.append(_hallazgo(
                    "eei-no-indicator", "medium", punto,
                    "EEI sin indicador: no se sabria cuando esta contestada"))
                continue
            for indicador in indicadores:
                valor = (indicador or {}).get("value") if isinstance(indicador, dict) else None
                fuente = (indicador or {}).get("source") if isinstance(indicador, dict) else None
                if not valor:
                    hallazgos.append(_hallazgo("indicator-no-value", "high", punto, "indicador sin valor"))
                if fuente is None:
                    hallazgos.append(_hallazgo(
                        "indicator-ungraded", "high", punto,
                        f"indicador {valor!r} sin graduar: la fuente va como A-F + 1-6"))
                elif not ADMIRALTY.match(str(fuente)):
                    hallazgos.append(_hallazgo(
                        "bad-admiralty", "medium", punto,
                        f"graduacion {fuente!r} fuera de la escala Admiralty (A2, B3, ...)"))

    altas = [h for h in hallazgos if h["severity"] == "high"]
    return {
        "valid": not altas,
        "findings": hallazgos,
        "requirements": len(requisitos),
        "high": len(altas),
        "medium": len(hallazgos) - len(altas),
    }
