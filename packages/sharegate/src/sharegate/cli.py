"""ShareGate command-line interface: check a product before it leaves the building."""

from __future__ import annotations

import argparse

from cti_method.contract import CANNOT_CHECK, FINDING, OK, emit, exit_code, read_text, run

from sharegate import __version__
from sharegate.core import check_tlp, pre_share, tlp_policy


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sharegate", description="Pre-share compliance gate (TLP 2.0 + STIX 2.1).")
    parser.add_argument("--version", action="version", version=f"sharegate {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    pre = sub.add_parser("check", help="Run the full gate on a file.")
    pre.add_argument("path", help="Path to a product or STIX bundle.")
    pre.add_argument("--today", metavar="AAAA-MM-DD", help="Check indicator expiry against this date.")
    tlp = sub.add_parser("tlp", help="Check only the TLP marking of a file.")
    tlp.add_argument("path")
    sub.add_parser("policy", help="Print the TLP 2.0 policy table.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "policy":
        emit(tlp_policy())
        return OK

    def body() -> int:
        text = read_text(args.path)
        if args.command == "tlp":
            result = check_tlp(text)
            emit(result)
            return OK if result["clean"] else FINDING
        result = pre_share(text, today=getattr(args, "today", None))
        emit(result)
        if result.get("checked") is False:
            return CANNOT_CHECK
        return exit_code(result["findings"])

    return run(body)


if __name__ == "__main__":
    raise SystemExit(main())
