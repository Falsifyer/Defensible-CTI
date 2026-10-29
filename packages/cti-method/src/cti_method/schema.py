"""The suite's published schemas, available from the installed package.

The schemas are the contract of the six formats, so they travel with the shared core
instead of living only in the repository: `--strict` has to be able to validate a document
on a machine where only the wheel is installed.
"""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from typing import Any

NAMES = (
    "pir",
    "assessment",
    "huntplan",
    "product",
    "judgement",
    "ledger-entry",
)

#: Where the published schema files resolve. The package copy is the source of truth;
#: this URL is the same file, not a second copy under ``/schemas``.
BASE_URL = (
    "https://raw.githubusercontent.com/Falsifyer/Defensible-CTI/main/"
    "packages/cti-method/src/cti_method/schemas"
)


def url(name: str) -> str:
    """The dereferenceable URL of one schema, congruent with its ``$id``."""
    if name not in NAMES:
        raise KeyError(f"unknown schema {name!r}; expected one of: {', '.join(NAMES)}")
    return f"{BASE_URL}/{name}.schema.json"


def directory() -> Path:
    """Filesystem path of the schema directory (works for editable and wheel installs)."""
    return Path(str(resources.files("cti_method").joinpath("schemas")))


def document(name: str) -> dict[str, Any]:
    """Load one schema by name (``judgement``, ``ledger-entry``, ...)."""
    if name not in NAMES:
        raise KeyError(f"unknown schema {name!r}; expected one of: {', '.join(NAMES)}")
    reference = resources.files("cti_method").joinpath("schemas", f"{name}.schema.json")
    return json.loads(reference.read_text(encoding="utf-8"))


def validate(instance: Any, name: str) -> None:
    """Validate a document against a schema. Raises ``RuntimeError`` if jsonschema is absent."""
    try:
        import jsonschema
    except ImportError as exc:  # pragma: no cover - exercised by the missing-extra path
        raise RuntimeError(
            "schema validation needs the 'schemas' extra: pip install 'cti-method[schemas]'"
        ) from exc
    jsonschema.Draft202012Validator(document(name)).validate(instance)
