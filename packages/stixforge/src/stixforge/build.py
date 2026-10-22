"""Turn a product document into a STIX 2.1 bundle.

The product is a JSON file: what the analyst wrote, the observables and the indicators,
and the TLP. The bundle is deterministic: the same product produces the same identifiers,
so rebuilding it does not create a second version of the same objects.
"""

from __future__ import annotations

import datetime as dt
import json
import uuid
from pathlib import Path
from typing import Any

from stixforge.markings import marking_object

# Namespace of this tool: identifiers are derived from it, never invented by hand.
NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "https://github.com/ME0094/stix-forge")

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


def _ahora() -> str:
    return dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _sco(observable: dict[str, Any]) -> dict[str, Any]:
    """Observable de STIX 2.1: inmutable, sin `created`, `modified` ni marcado propio.

    Los SCO dejaron de llevar esas propiedades en 2.1; el marcado va en los SDO (el report
    y los indicadores) que los referencian. Emitirlas hacía el bundle invalido para
    `stix2.parse`, que es como se descubrio.
    """
    tipo = observable.get("type")
    if tipo not in SCO_TYPES:
        raise ValueError(f"unsupported observable type: {tipo!r}")
    campo = SCO_TYPES[tipo]
    valor = observable.get(campo)
    if not valor:
        raise ValueError(f"observable {tipo} needs {campo!r}")
    clave = json.dumps(valor, sort_keys=True) if isinstance(valor, dict) else str(valor)
    return {
        "type": tipo,
        "spec_version": "2.1",
        "id": _id(tipo, clave),
        campo: valor,
    }


def build(producto: dict[str, Any]) -> dict[str, Any]:
    """Build the bundle. Raises ValueError with the reason if the product is not usable."""
    titulo = (producto.get("title") or "").strip()
    if not titulo:
        raise ValueError("the product needs a title")
    autor_nombre = (producto.get("author") or "").strip()
    if not autor_nombre:
        raise ValueError("the product needs an author: the bundle must say who says this")

    sello = producto.get("created") or _ahora()
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
        objetos.append({
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
            "valid_from": indicador.get("valid_from") or sello,
            "indicator_types": indicador.get("indicator_types", ["malicious-activity"]),
        })
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
    objetos.append({
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
        **({"description": producto["summary"]} if producto.get("summary") else {}),
    })

    return {
        "type": "bundle",
        "id": f"bundle--{uuid.uuid5(NAMESPACE, 'bundle|' + report_id)}",
        "objects": objetos,
    }


def build_file(entrada: str | Path, salida: str | Path | None = None) -> dict[str, Any]:
    producto = json.loads(Path(entrada).read_text(encoding="utf-8"))
    bundle = build(producto)
    if salida:
        Path(salida).write_text(json.dumps(bundle, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return bundle
