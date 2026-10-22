"""HuntPlan command-line interface."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from huntplan import __version__
from huntplan.core import data_sources_for, hmm_levels, validate_hypothesis


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="huntplan", description="Turn a question into a falsifiable hunt plan.")
    parser.add_argument("--version", action="version", version=f"huntplan {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="Check a hypothesis file for falsifiability.")
    validate.add_argument("path", help="Path to a text file holding the hypothesis.")
    sources = sub.add_parser("sources", help="Print the data sources required by a technique.")
    sources.add_argument("technique_id", help="ATT&CK technique ID, e.g. T1059.")
    sub.add_parser("hmm", help="Print the Hunting Maturity Model levels.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "hmm":
        print(json.dumps(hmm_levels(), indent=2, ensure_ascii=False))
        return 0
    if args.command == "sources":
        result = data_sources_for(args.technique_id)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result["known"] else 1
    result = validate_hypothesis(Path(args.path).read_text(encoding="utf-8"))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["falsifiable"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
