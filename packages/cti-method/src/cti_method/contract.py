"""The house contract: severities, findings, exit codes and the file boundary.

Every command in the suite returns the same three codes and says the same three things
about a finding. Keeping it here, once, is what makes the contract true of the six tools
instead of true of whichever one remembered to implement it:

* ``0`` — clean, or only medium/low findings;
* ``1`` — a high finding, i.e. the tool refuses what it was given;
* ``2`` — the tool could not check. **Not checked is not clean.**

Unreadable, undecodable or structurally impossible input is a ``CannotCheck``: it maps to
``2``, never to ``1``. A missing file is not an infraction committed by the file.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

OK = 0
FINDING = 1
CANNOT_CHECK = 2

HIGH = "high"
MEDIUM = "medium"
LOW = "low"
SEVERITIES = (HIGH, MEDIUM, LOW)


class CannotCheck(Exception):
    """Raised when the tool cannot look at the input at all (exit code 2)."""


def finding(
    code: str,
    severity: str,
    message: str,
    *,
    pointer: str | None = None,
    where: str | None = None,
) -> dict[str, str]:
    """One finding, with the same keys everywhere.

    ``pointer`` is a JSON Pointer for a document; ``where`` is a human locator for a
    flat one. Both are optional and both survive to the output unchanged.
    """
    if severity not in SEVERITIES:
        raise ValueError(f"unknown severity {severity!r}")
    item = {"code": code, "severity": severity, "message": message}
    if pointer:
        item["pointer"] = pointer
    if where:
        item["where"] = where
    return item


def severity_counts(findings: Sequence[dict[str, str]]) -> dict[str, int]:
    return {level: sum(1 for item in findings if item["severity"] == level) for level in SEVERITIES}


def has_high(findings: Sequence[dict[str, str]]) -> bool:
    return any(item["severity"] == HIGH for item in findings)


def read_text(path: str | Path) -> str:
    """Read a text file, or fail closed with ``CannotCheck``."""
    target = Path(path)
    try:
        return target.read_text(encoding="utf-8")
    except OSError as exc:
        raise CannotCheck(f"cannot read {target}: {exc.strerror or exc}") from exc
    except UnicodeDecodeError as exc:
        raise CannotCheck(f"cannot decode {target} as UTF-8") from exc


def read_json(path: str | Path) -> Any:
    """Read a JSON document, or fail closed with ``CannotCheck``."""
    text = read_text(path)
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise CannotCheck(f"{path} is not valid JSON: {exc.msg} (line {exc.lineno})") from exc


def emit(document: Any) -> None:
    """Print a JSON document, one encoding everywhere (UTF-8, no ASCII escaping)."""
    print(json.dumps(document, indent=2, ensure_ascii=False))


def write(document: Any, path: str | Path | None) -> None:
    """Write a JSON document to ``path``, or print it when ``path`` is ``None``."""
    if path is None:
        emit(document)
        return
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run(main: Callable[[], int]) -> int:
    """Run a command body, mapping ``CannotCheck`` to exit code 2.

    A command that wants its own CLI error handling can call ``cannot_check`` directly;
    everything else can let the exception out through this wrapper.
    """
    try:
        return main()
    except CannotCheck as exc:
        print(f"cannot check: {exc}", file=sys.stderr)
        return CANNOT_CHECK


def exit_code(findings: Sequence[dict[str, str]]) -> int:
    """The house rule: a high finding refuses (1); anything else is clean (0)."""
    return FINDING if has_high(findings) else OK
