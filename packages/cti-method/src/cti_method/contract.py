"""The house contract: severities, findings, exit codes and the file boundary.

Every command in the suite returns the same three codes and says the same three things
about a finding. Keeping it here, once, is what makes the contract true of the six tools
instead of true of whichever one remembered to implement it:

* ``0`` — clean, or only medium/low findings;
* ``1`` — a high finding, i.e. the tool refuses what it was given;
* ``2`` — the tool could not check. **Not checked is not clean.**

Unreadable, undecodable, oversized or structurally impossible input is a ``CannotCheck``:
it maps to ``2``, never to ``1``. A missing file is not an infraction committed by the
file.

The size and depth limits are part of the boundary, not a hardening afterthought: a tool
that reads whatever it is handed can be exhausted by a 2 GB JSON document, and "the tool
crashed" is not a finding either.
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

#: Largest input the suite will read in one go (bytes).
MAX_BYTES = 8 * 1024 * 1024
#: Deepest JSON nesting accepted. STIX and the suite's documents are shallow; a document
#: deeper than this is malformed or hostile.
MAX_DEPTH = 64


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


def read_text(path: str | Path, *, limit: int = MAX_BYTES) -> str:
    """Read a text file, or fail closed with ``CannotCheck``."""
    target = Path(path)
    try:
        size = target.stat().st_size
    except OSError as exc:
        raise CannotCheck(f"cannot read {target}: {exc.strerror or exc}") from exc
    if size > limit:
        raise CannotCheck(f"{target} is {size:,} bytes, over the {limit:,}-byte limit")
    try:
        return target.read_text(encoding="utf-8")
    except OSError as exc:
        raise CannotCheck(f"cannot read {target}: {exc.strerror or exc}") from exc
    except UnicodeDecodeError as exc:
        raise CannotCheck(f"cannot decode {target} as UTF-8") from exc


def nesting_depth(value: Any, limit: int = MAX_DEPTH) -> int:
    """Depth of a parsed JSON value, or ``limit + 1`` as soon as it exceeds ``limit``."""
    deepest = 0
    stack: list[tuple[Any, int]] = [(value, 1)]
    while stack:
        current, depth = stack.pop()
        if depth > deepest:
            deepest = depth
            if deepest > limit:
                return deepest
        if isinstance(current, dict):
            stack.extend((item, depth + 1) for item in current.values())
        elif isinstance(current, list):
            stack.extend((item, depth + 1) for item in current)
    return deepest


def read_json(path: str | Path, *, limit: int = MAX_BYTES, max_depth: int = MAX_DEPTH) -> Any:
    """Read a JSON document, or fail closed with ``CannotCheck``."""
    text = read_text(path, limit=limit)
    try:
        document = json.loads(text)
    except json.JSONDecodeError as exc:
        raise CannotCheck(f"{path} is not valid JSON: {exc.msg} (line {exc.lineno})") from exc
    if nesting_depth(document, max_depth) > max_depth:
        raise CannotCheck(f"{path} nests deeper than the {max_depth}-level limit")
    return document


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
