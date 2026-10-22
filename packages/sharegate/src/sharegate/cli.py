"""ShareGate command-line interface: check a product before it leaves the building."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sharegate import __version__
from sharegate.core import check_tlp, pre_share, tlp_policy


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sharegate", description="Pre-share compliance gate (TLP 2.0 + STIX 2.1).")
    parser.add_argument("--version", action="version", version=f"sharegate {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    pre = sub.add_parser("check", help="Run the full gate on a file.")
    pre.add_argument("path", help="Path to a product or STIX bundle.")
    tlp = sub.add_parser("tlp", help="Check only the TLP marking of a file.")
    tlp.add_argument("path")
    sub.add_parser("policy", help="Print the TLP 2.0 policy table.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "policy":
        print(json.dumps(tlp_policy(), indent=2, ensure_ascii=False))
        return 0
    text = Path(args.path).read_text(encoding="utf-8")
    if args.command == "tlp":
        result = check_tlp(text)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result["clean"] else 1
    result = pre_share(text)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["shareable"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
