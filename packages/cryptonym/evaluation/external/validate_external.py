#!/usr/bin/env python3
"""Validate an external corpus before it becomes evidence about the method.

This is the executable checklist for phases 1–2 of ``PROTOCOL.md``. It is deliberately
separate from the engine: it checks the corpus shape, the placeholders, the two adjudicators
and the source graph, and it exits with the house codes (0 clean, 1 a high finding, 2 it
could not check).

Usage (from ``packages/cryptonym``)::

    python evaluation/external/validate_external.py evaluation/external/corpus.json
    python evaluation/external/validate_external.py evaluation/external/corpus.json --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from cryptonym.evaluate.adjudication import (  # noqa: E402
    Adjudication,
    filter_adjudication,
    validate_corpus,
)

BINARY = {"same_actor", "distinct"}
BAD_STANDARDS = {"author-assertion", "single-source"}
PLACEHOLDERS = ("REPLACE-ME", "REPLACE-", "TEMPLATE", "example.invalid")


def finding(code: str, severity: str, message: str, *, where: str | None = None) -> dict[str, str]:
    item = {"code": code, "severity": severity, "message": message}
    if where:
        item["where"] = where
    return item


def _strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [text for item in value.values() for text in _strings(item)]
    if isinstance(value, list):
        return [text for item in value for text in _strings(item)]
    return []


def _check_schema(document: dict[str, Any], schema_path: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    try:
        import jsonschema
    except ImportError:
        raise RuntimeError(
            "jsonschema is not installed: pip install 'cti-method[schemas]' or the dev group"
        ) from None
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema.Draft202012Validator(
            schema, format_checker=jsonschema.FormatChecker()
        ).validate(document)
    except jsonschema.ValidationError as exc:
        pointer = "/".join(str(item) for item in exc.absolute_path)
        findings.append(
            finding(
                "schema",
                "high",
                exc.message,
                where=pointer or None,
            )
        )
    except (OSError, ValueError) as exc:
        raise RuntimeError(f"cannot read {schema_path}: {type(exc).__name__}") from exc
    return findings


def check(document: dict[str, Any], schema_path: Path) -> list[dict[str, str]]:
    findings = _check_schema(document, schema_path)
    cases = document.get("cases") or []
    if not isinstance(cases, list):
        return findings

    findings.extend(
        finding("corpus", "high", problem) for problem in validate_corpus(document)
    )

    seen: set[str] = set()
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            continue
        where = str(case.get("id") or f"cases[{index}]")
        if case.get("id") in seen:
            findings.append(finding("duplicate-id", "high", "duplicate case id", where=where))
        seen.add(str(case.get("id") or ""))

        for text in _strings(case):
            for placeholder in PLACEHOLDERS:
                if placeholder in text:
                    findings.append(
                        finding(
                            "placeholder",
                            "high",
                            f"placeholder {placeholder!r} is still present",
                            where=where,
                        )
                    )
                    break

        adjudication = case.get("adjudication")
        if not isinstance(adjudication, dict):
            continue
        truth = adjudication.get("truth")
        if truth not in BINARY:
            continue

        adjudicators = {
            str(item).strip()
            for item in adjudication.get("adjudicators") or []
            if str(item).strip()
        }
        if len(adjudicators) < 2:
            findings.append(
                finding(
                    "binary-adjudicators",
                    "high",
                    f"a binary truth needs two independent adjudicators; found {len(adjudicators)}",
                    where=where,
                )
            )

        standard = adjudication.get("standard")
        if standard in BAD_STANDARDS:
            findings.append(
                finding(
                    "binary-standard",
                    "high",
                    f"standard {standard!r} is never admissible for a binary truth",
                    where=where,
                )
            )

        try:
            verdict = filter_adjudication(Adjudication.from_dict(adjudication))
        except (KeyError, ValueError) as exc:
            findings.append(
                finding(
                    "adjudication",
                    "high",
                    f"cannot apply the adjudication filter: {type(exc).__name__}: {exc}",
                    where=where,
                )
            )
            continue
        if not verdict.admissible:
            findings.append(
                finding(
                    "binary-not-earned",
                    "high",
                    "the binary truth is not admissible: " + "; ".join(verdict.reasons),
                    where=where,
                )
            )
        if verdict.independent_sources < 2:
            findings.append(
                finding(
                    "binary-sources",
                    "high",
                    f"a binary truth needs two independent sources; found {verdict.independent_sources}",
                    where=where,
                )
            )

    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="validate_external",
        description="Validate an external adjudicated corpus against PROTOCOL.md.",
    )
    parser.add_argument("path", help="The corpus JSON to validate.")
    parser.add_argument(
        "--schema",
        default=str(Path(__file__).with_name("schema.json")),
        help="The JSON Schema (default: the sibling schema.json).",
    )
    parser.add_argument("--json", action="store_true", dest="as_json", help="Machine-readable output.")
    args = parser.parse_args(argv)

    try:
        document = json.loads(Path(args.path).read_text(encoding="utf-8"))
    except OSError as exc:
        print(f"cannot check: cannot read {args.path}: {exc.strerror or exc}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"cannot check: {args.path} is not valid JSON: {exc.msg}", file=sys.stderr)
        return 2
    if not isinstance(document, dict):
        print(f"cannot check: {args.path} is not a JSON object", file=sys.stderr)
        return 2

    try:
        findings = check(document, Path(args.schema))
    except RuntimeError as exc:
        print(f"cannot check: {exc}", file=sys.stderr)
        return 2

    high = sum(1 for item in findings if item["severity"] == "high")
    payload = {
        "path": args.path,
        "valid": high == 0,
        "cases": len(document.get("cases") or []),
        "high": high,
        "findings": findings,
    }
    if args.as_json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        for item in findings:
            where = f" [{item['where']}]" if item.get("where") else ""
            print(f"  {item['severity'].upper():6s} {item['code']:24s}{where} {item['message']}")
        print(
            f"\n{payload['cases']} case(s); "
            f"{'clean' if high == 0 else f'{high} high finding(s)'}"
        )
    return 0 if high == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
