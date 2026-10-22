"""Structural validation of a STIX 2.1 bundle, and an optional external check.

The structural check is **not** implemented here: it is :func:`cti_method.stix.validate_bundle`,
the same one the gate calls, so the factory and the gate cannot disagree about what a
valid bundle is. What lives here is the optional external check.

With ``--external`` the file is handed to the OASIS tooling. If none is installed, the
exit code is 2: not checked is not clean.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from cti_method.stix import validate_bundle

__all__ = ["external", "validate"]


def validate(bundle: dict[str, Any], today: str | None = None) -> dict[str, Any]:
    """Return findings and whether the bundle is shareable."""
    return validate_bundle(bundle, today=today)


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
