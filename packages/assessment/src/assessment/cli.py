"""assessment-mcp command-line interface."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from assessment import __version__
from assessment.core import assess, grade, read_ledger


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="assessment", description="Grade any claim, and keep a ledger.")
    parser.add_argument("--version", action="version", version=f"assessment {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    grade_cmd = sub.add_parser("grade", help="Grade a claim on two axes.")
    grade_cmd.add_argument("--confidence", required=True, choices=["high", "moderate", "low"])
    grade_cmd.add_argument("--probability", default=None)

    assess_cmd = sub.add_parser("assess", help="Grade a full claim from a JSON document.")
    assess_cmd.add_argument("path")

    ledger = sub.add_parser("ledger", help="Read a ledger of graded claims.")
    ledger.add_argument("path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "grade":
        print(json.dumps(grade(args.confidence, args.probability), indent=2, ensure_ascii=False))
        return 0
    if args.command == "assess":
        document = json.loads(Path(args.path).read_text(encoding="utf-8"))
        print(json.dumps(assess(document), indent=2, ensure_ascii=False))
        return 0
    print(json.dumps(read_ledger(args.path), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
