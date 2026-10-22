"""Turn a product document into a STIX 2.1 bundle.

The product is a JSON file: what the analyst wrote, the observables and the indicators,
the TLP, the creation timestamp, and the identifiers of the steps the product answers.
The bundle is **byte-reproducible**: identifiers are derived from content and ``created``
is required, so rebuilding the same product does not create a second version of the same
objects with a different timestamp under one id.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from cti_method.stix import marking_object
from cti_method.trace import external_references

# Namespace of this tool: identifiers are derived from it, never invented by hand.
NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "https://github.com/ME0094/cti-suite")

SCO_TYPES = {
    "domain-name": "value",
    "ipv4-addr": "value",
    "ipv6-addr": "value",
    "url": "value",
    "file": "hashes",
    "email-addr": "value",
    "mac-addr": "value",
    "windows-registry-key": "key",
}


def _id(tipo: str, clave: str) -> str:
    return f"{tipo}--{uuid.uuid5(NAMESPACE, f'{tipo}|{clave}')}"


def _sco(observable: dict[str, Any]) -> dict[str, Any]:
    """A STIX 2.1 cyber-observable: immutable, with no `created`, `modified` or marking.

    SCOs stopped carrying those properties in 2.1; the marking goes on the SDOs (the report
    and the indicators) that reference them. Emitting them made the bundle invalid for
    `stix2.parse`, which is how it was found.
    """
    tipo = observable.get("type")
    if tipo not in SCO_TYPES:
        raise ValueError(f"unsupported observable type: {tipo!r}")
    campo = SCO_TYPES[tipo]
    valor = observable.get(campo)
    if not valor:
        raise ValueError(f"observable {tipo} needs {campo!r}")
    clave = json.dumps(valor, sort_keys=True) if isinstance(valor, dict) else str(valor)
    objeto = {"type": tipo, "spec_version": "2.1", "id": _id(tipo, clave)}
    objeto[campo] = valor
    return objeto


def _confidence(value: Any) -> int | None:
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 100:
        raise ValueError("confidence must be an integer between 0 and 100")
    return value


def build(
    producto: dict[str, Any],
    trace: dict[str, str | None] | None = None,
    trace_hashes: dict[str, str | None] | None = None,
) -> dict[str, Any]:
    """Build the bundle. Raises ValueError with the reason if the product is not usable.

    ``trace`` carries the verified identifiers of the upstream artifacts
    (``requirement_id``, ``assessment_id``, ``hunt_id``); they are emitted as
    ``external_references`` on the report so a consumer can walk back to the evidence.
    """
    titulo = (producto.get("title") or "").strip()
    if not titulo:
        raise ValueError("the product needs a title")
    autor_nombre = (producto.get("author") or "").strip()
    if not autor_nombre:
        raise ValueError("the product needs an author: the bundle must say who says this")

    sello = (producto.get("created") or "").strip()
    if not sello:
        raise ValueError(
            "the product needs created (ISO 8601 UTC, ending in Z): without it the same "
            "identifiers would be stamped with a new timestamp on every build"
        )
    if not sello.endswith("Z"):
        raise ValueError("created must be an ISO 8601 UTC timestamp (ending in Z)")

    marcado = marking_object(producto.get("tlp") or "clear")
    id_autor = _id("identity", autor_nombre)
    objetos: list[dict[str, Any]] = [
        marcado,
        {
            "type": "identity",
            "spec_version": "2.1",
            "id": id_autor,
            "created": sello,
            "modified": sello,
            "name": autor_nombre,
            "identity_class": producto.get("author_class", "individual"),
            "object_marking_refs": [marcado["id"]],
        },
    ]

    referencias: list[str] = []
    for observable in producto.get("observables") or []:
        sco = _sco(observable)
        objetos.append(sco)
        referencias.append(sco["id"])

    for indicador in producto.get("indicators") or []:
        patron = (indicador.get("pattern") or "").strip()
        if not patron:
            raise ValueError("every indicator needs a STIX pattern")
        ident = _id("indicator", f"{indicador.get('name', '')}|{patron}")
        valido_hasta = indicador.get("valid_until") or producto.get("valid_until")
        valido_desde = indicador.get("valid_from") or sello
        if valido_hasta and str(valido_hasta) < str(valido_desde):
            raise ValueError(f"indicator {indicador.get('name')!r}: valid_until is before valid_from")
        objeto = {
            "type": "indicator",
            "spec_version": "2.1",
            "id": ident,
            "created": sello,
            "modified": sello,
            "created_by_ref": id_autor,
            "object_marking_refs": [marcado["id"]],
            "name": indicador.get("name") or patron,
            "pattern": patron,
            "pattern_type": indicador.get("pattern_type", "stix"),
            "valid_from": valido_desde,
            "indicator_types": indicador.get("indicator_types", ["malicious-activity"]),
        }
        if valido_hasta:
            objeto["valid_until"] = valido_hasta
        confianza = _confidence(indicador.get("confidence"))
        if confianza is not None:
            objeto["confidence"] = confianza
        objetos.append(objeto)
        referencias.append(ident)

    for malware in producto.get("malware") or []:
        nombre = (malware.get("name") or "").strip()
        if not nombre:
            raise ValueError("every malware object needs a name")
        ident = _id("malware", nombre)
        objetos.append({
            "type": "malware",
            "spec_version": "2.1",
            "id": ident,
            "created": sello,
            "modified": sello,
            "created_by_ref": id_autor,
            "object_marking_refs": [marcado["id"]],
            "name": nombre,
            "is_family": bool(malware.get("is_family", False)),
            "malware_types": malware.get("malware_types", ["unknown"]),
        })
        referencias.append(ident)

    if not referencias:
        raise ValueError("the product has nothing to share: add observables, indicators or malware")

    report_id = _id("report", producto.get("id") or titulo)
    report = {
        "type": "report",
        "spec_version": "2.1",
        "id": report_id,
        "created": sello,
        "modified": sello,
        "created_by_ref": id_autor,
        "object_marking_refs": [marcado["id"]],
        "name": titulo,
        "published": producto.get("published") or sello,
        "report_types": producto.get("report_types", ["threat-report"]),
        "object_refs": referencias,
    }
    if producto.get("summary"):
        report["description"] = producto["summary"]
    referencias_externas = external_references(trace or {}, trace_hashes)
    if referencias_externas:
        report["external_references"] = referencias_externas
    objetos.append(report)

    return {
        "type": "bundle",
        "id": f"bundle--{uuid.uuid5(NAMESPACE, 'bundle|' + report_id)}",
        "objects": objetos,
    }


def build_file(
    source: str | Path,
    output: str | Path | None = None,
    trace: dict[str, str | None] | None = None,
) -> dict[str, Any]:
    product = json.loads(Path(source).read_text(encoding="utf-8"))
    bundle = build(product, trace=trace)
    if output:
        Path(output).write_text(json.dumps(bundle, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return bundle
