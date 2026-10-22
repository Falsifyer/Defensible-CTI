"""Structural validation of a STIX 2.1 bundle, and an optional external check.

The internal check answers one question: is this bundle coherent enough to be shared? The
external check, with ``--external``, hands the file to ``stix2-validator``. If that tool is
not installed, the exit code is 2: not checked is not clean.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ID = re.compile(r"^(?P<tipo>[a-z0-9-]+)--[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
# marking-definition no lleva `modified`: es un objeto de la especificacion con `created`
# unicamente, y exigirlo hacia fallar todos los bundles con marcado.
REQUIRED = ("type", "spec_version", "id", "created", "modified")
REQUIRED_SIN_MODIFIED = {"marking-definition"}
# Los cyber-observables de 2.1 son inmutables: solo type, spec_version, id y su valor.
SCO = {
    "domain-name", "ipv4-addr", "ipv6-addr", "url", "file", "email-addr", "mac-addr",
    "windows-registry-key", "user-account", "x509-certificate", "mutex", "process",
}
MARKED = {"indicator", "malware", "report", "identity", "threat-actor", "campaign", "tool"}


def _hallazgo(codigo: str, severidad: str, donde: str, mensaje: str) -> dict[str, str]:
    return {"code": codigo, "severity": severidad, "where": donde, "message": mensaje}


def validate(bundle: dict[str, Any]) -> dict[str, Any]:
    """Return findings and whether the bundle is shareable."""
    hallazgos: list[dict[str, str]] = []

    if bundle.get("type") != "bundle":
        hallazgos.append(_hallazgo("not-a-bundle", "high", "root", "the document is not a bundle"))
        return {"valid": False, "findings": hallazgos, "objects": 0, "high": 1, "medium": 0}

    objetos = bundle.get("objects")
    if not isinstance(objetos, list) or not objetos:
        hallazgos.append(_hallazgo("empty-bundle", "high", "objects", "the bundle has no objects"))
        return {"valid": False, "findings": hallazgos, "objects": 0, "high": 1, "medium": 0}

    if not ID.match(str(bundle.get("id", ""))) or not str(bundle.get("id", "")).startswith("bundle--"):
        hallazgos.append(_hallazgo("bad-bundle-id", "high", "root", "bundle id missing or not a bundle-- UUID"))

    por_id: dict[str, dict[str, Any]] = {}
    for i, obj in enumerate(objetos):
        donde = f"objects[{i}]"
        if not isinstance(obj, dict):
            hallazgos.append(_hallazgo("malformed", "high", donde, "object is not a JSON object"))
            continue
        tipo = obj.get("type") or "?"
        donde = f"{tipo} {obj.get('id', '?')}"[:80]
        if tipo in SCO:
            exigidos = ["type", "spec_version", "id"]
        elif tipo in REQUIRED_SIN_MODIFIED:
            exigidos = [c for c in REQUIRED if c != "modified"]
        else:
            exigidos = list(REQUIRED)
        faltan = [c for c in exigidos if not obj.get(c)]
        if faltan:
            hallazgos.append(_hallazgo(
                "missing-property", "high", donde, "missing: " + ", ".join(faltan)))
        ident = obj.get("id")
        if isinstance(ident, str):
            m = ID.match(ident)
            if not m:
                hallazgos.append(_hallazgo("bad-id", "high", donde, "id is not <type>--<uuid>"))
            elif m.group("tipo") != tipo:
                hallazgos.append(_hallazgo(
                    "id-type-mismatch", "high", donde, "the id type does not match the object type"))
            if ident in por_id:
                hallazgos.append(_hallazgo("duplicate-id", "high", donde, "identifier repeated"))
            por_id[ident] = obj
        if obj.get("spec_version") not in ("2.1", None):
            hallazgos.append(_hallazgo(
                "bad-spec-version", "medium", donde, f"spec_version {obj.get('spec_version')!r}"))

    # Referencias que no resuelven dentro del bundle.
    for obj in objetos:
        if not isinstance(obj, dict):
            continue
        donde = f"{obj.get('type')} {obj.get('id', '?')}"[:80]
        for campo in ("object_refs", "object_marking_refs"):
            for ref in obj.get(campo) or []:
                if ref not in por_id:
                    hallazgos.append(_hallazgo(
                        "unresolved-reference", "high", donde, f"{campo} -> {ref} is not in the bundle"))
        creado = obj.get("created_by_ref")
        if creado and creado not in por_id:
            hallazgos.append(_hallazgo(
                "unresolved-reference", "high", donde, f"created_by_ref -> {creado} is not in the bundle"))

    # Sin marcado no hay decision de comparticion: el producto no es compartible.
    marcados = [o for o in objetos if isinstance(o, dict) and o.get("type") in MARKED]
    sin_marcar = [o for o in marcados if not o.get("object_marking_refs")]
    if sin_marcar:
        hallazgos.append(_hallazgo(
            "no-marking", "high", f"{len(sin_marcar)} object(s)",
            "objects with no TLP marking: the bundle does not say how far it may travel"))
    if not any(isinstance(o, dict) and o.get("type") == "marking-definition" for o in objetos):
        hallazgos.append(_hallazgo(
            "no-marking-definition", "medium", "objects",
            "the TLP marking is referenced but not defined in the bundle"))

    altas = [h for h in hallazgos if h["severity"] == "high"]
    medias = [h for h in hallazgos if h["severity"] == "medium"]
    return {
        "valid": not altas,
        "findings": hallazgos,
        "objects": len(objetos),
        "high": len(altas),
        "medium": len(medias),
    }


def external(bundle: dict, path: str | Path) -> dict:
    """Comprueba el bundle con lo que haya instalado fuera de este paquete.

    Dos comprobadores, y cualquiera de los dos vale:
      - `stix2` (la biblioteca de OASIS): parsea el bundle contra su modelo de objetos.
        No necesita red.
      - `stix2-validator`: valida contra los esquemas JSON. Necesita su cache de esquemas,
        que descarga; sin cache no puede decir nada y eso **no** es un aprobado.

    Devuelve `{"available": False}` cuando no hay ninguno.
    """
    resultado: dict = {"available": True, "library": None, "validator": None}

    try:
        import stix2

        stix2.parse(bundle, allow_custom=False, version="2.1")
        resultado["library"] = {"tool": f"stix2 {stix2.__version__}", "ok": True}
    except ImportError:
        pass
    except Exception as exc:  # noqa: BLE001 - cualquier fallo del modelo es un hallazgo
        resultado["library"] = {"tool": "stix2", "ok": False, "error": str(exc)[:800]}

    ejecutable = shutil.which("stix2_validator") or shutil.which("stix2-validator")
    if ejecutable is None:
        al_lado = Path(sys.executable).parent
        for nombre in ("stix2_validator", "stix2-validator"):
            candidato = al_lado / nombre
            if candidato.is_file():
                ejecutable = str(candidato)
                break
    if ejecutable:
        proceso = subprocess.run(
            [ejecutable, str(path)], capture_output=True, text=True, timeout=180, check=False,
        )
        resultado["validator"] = {
            "tool": Path(ejecutable).name,
            "code": proceso.returncode,
            "output": (proceso.stdout + proceso.stderr).strip()[:4000],
        }

    if resultado["library"] is None and resultado["validator"] is None:
        return {"available": False}
    return resultado
