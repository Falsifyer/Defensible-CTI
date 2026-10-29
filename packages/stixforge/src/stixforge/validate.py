"""Structural validation of a STIX 2.1 bundle, and an optional external check.

The structural check is **not** implemented here: it is :func:`cti_method.stix.validate_bundle`,
the same one the gate calls, so the factory and the gate cannot disagree about what a
valid bundle is. What lives here is the optional external check.

With ``--external`` the bundle is checked against the vendored OASIS STIX 2.1 JSON schemas
(offline, no cache). The ``stix2`` parse and the optional ``stix2-validator`` are reported
separately. If the vendored schema check cannot run and no other checker ran, the exit code
is 2: not checked is not clean.
"""

from __future__ import annotations

import json
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


def _schema_dir() -> Path:
    return Path(__file__).resolve().parent / "schemas" / "stix2.1"


def schema_validate(bundle: dict[str, Any]) -> dict[str, Any]:
    """Validate a bundle against the vendored OASIS STIX 2.1 JSON schemas.

    The schemas travel with the wheel, so this check is offline and deterministic. It is
    deliberately separate from the structural validator in ``cti_method``: this one is the
    external standard, not the suite's own rules.
    """
    try:
        from jsonschema import Draft202012Validator
        from referencing import Registry, Resource
        from referencing.jsonschema import DRAFT202012
    except ImportError:
        return {
            "checked": False,
            "ok": False,
            "tool": "OASIS STIX 2.1 schemas (vendored)",
            "errors": ["jsonschema/referencing is not installed"],
        }

    directory = _schema_dir()
    resources: list[tuple[str, Any]] = []
    schemas: dict[str, dict[str, Any]] = {}
    by_type: dict[str, str] = {}
    object_types = {"sdos", "sros", "observables"}
    object_common = {"marking-definition", "extension-definition", "language-content"}
    try:
        for path in sorted(directory.rglob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            uri = data.get("$id")
            if not uri:
                continue
            resources.append(
                (uri, Resource.from_contents(data, default_specification=DRAFT202012))
            )
            schemas[uri] = data
            is_object = path.parent.name in object_types
            is_common_object = path.parent.name == "common" and path.stem in object_common
            if is_object or is_common_object:
                by_type[path.stem] = uri
    except (OSError, ValueError) as exc:
        return {
            "checked": False,
            "ok": False,
            "tool": "OASIS STIX 2.1 schemas (vendored)",
            "errors": [f"cannot load vendored schemas: {type(exc).__name__}: {exc}"],
        }

    registry = Registry().with_resources(resources)
    errors: list[str] = []

    try:
        bundle_schema = next(
            (schema for uri, schema in schemas.items() if uri.endswith("/common/bundle.json")),
            None,
        )
        if bundle_schema:
            for error in Draft202012Validator(bundle_schema, registry=registry).iter_errors(bundle):
                location = "/".join(str(item) for item in error.absolute_path)
                errors.append(f"bundle{('/' + location) if location else ''}: {error.message}")

        for index, obj in enumerate(bundle.get("objects") or []):
            if not isinstance(obj, dict):
                continue
            object_type = obj.get("type")
            uri = by_type.get(str(object_type))
            if uri is None:
                errors.append(f"objects[{index}]: no OASIS schema for type {object_type!r}")
                continue
            validator = Draft202012Validator(schemas[uri], registry=registry)
            for error in validator.iter_errors(obj):
                location = "/".join(str(item) for item in error.absolute_path)
                errors.append(
                    f"objects[{index}] {object_type}"
                    f"{('/' + location) if location else ''}: {error.message}"
                )
    except Exception as exc:  # noqa: BLE001 - any failure of the checker is not a pass
        return {
            "checked": False,
            "ok": False,
            "tool": "OASIS STIX 2.1 schemas (vendored)",
            "errors": [f"schema validation failed: {type(exc).__name__}: {exc}"],
        }

    return {
        "checked": True,
        "ok": not errors,
        "tool": "OASIS STIX 2.1 schemas (vendored)",
        "errors": errors[:25],
        "truncated": len(errors) > 25,
    }


def external(bundle: dict, path: str | Path) -> dict:
    """Check the bundle against the vendored OASIS schemas and any optional tooling.

    The vendored OASIS JSON schemas are checked first; they need no network or cache.
    ``stix2`` (object model) and ``stix2-validator`` (its own schema cache) are optional
    additional checks. Returns ``{"available": False}`` when none of the three ran.
    """
    result: dict = {
        "available": True,
        "schema": schema_validate(bundle),
        "library": None,
        "validator": None,
    }

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

    if (
        result["library"] is None
        and result["validator"] is None
        and not result["schema"].get("checked", False)
    ):
        return {"available": False}
    return result
