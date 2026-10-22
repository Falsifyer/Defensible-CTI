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
    """Check the bundle with whatever is installed outside this package.

    Two checkers, and either one is enough:
      - `stix2` (the OASIS library): parses the bundle against its object model.
        It needs no network.
      - `stix2-validator`: validates against the JSON schemas. It needs its schema cache,
        which it downloads; without the cache it cannot say anything and that is **not**
        a pass.

    Returns `{"available": False}` when neither is installed.
    """
    result: dict = {"available": True, "library": None, "validator": None}

    try:
        import stix2

        stix2.parse(bundle, allow_custom=False, version="2.1")
        result["library"] = {"tool": f"stix2 {stix2.__version__}", "ok": True}
    except ImportError:
        pass
    except Exception as exc:  # noqa: BLE001 - any failure of the model is a finding
        result["library"] = {"tool": "stix2", "ok": False, "error": str(exc)[:800]}

    executable = shutil.which("stix2_validator") or shutil.which("stix2-validator")
    if executable is None:
        beside = Path(sys.executable).parent
        for name in ("stix2_validator", "stix2-validator"):
            candidate = beside / name
            if candidate.is_file():
                executable = str(candidate)
                break
    if executable:
        process = subprocess.run(
            [executable, str(path)], capture_output=True, text=True, timeout=180, check=False,
        )
        result["validator"] = {
            "tool": Path(executable).name,
            "code": process.returncode,
            "output": (process.stdout + process.stderr).strip()[:4000],
        }

    if result["library"] is None and result["validator"] is None:
        return {"available": False}
    return result
