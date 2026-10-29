"""ctisuite command line: one report from the artifacts, and the whole cycle in one command."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cti_method.contract import CANNOT_CHECK, FINDING, OK, CannotCheck, emit, read_json, run
from cti_method.stix import effective_marking

from cti_suite import __version__
from cti_suite.report import missing_artifacts, render_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ctisuite", description="The cycle as one artifact.")
    parser.add_argument("--version", action="version", version=f"cti-suite {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    report = sub.add_parser("report", help="Render the cycle as one markdown product.")
    report.add_argument("--pir", metavar="PATH", help="The PIR register.")
    report.add_argument("--assessment", metavar="PATH", help="The graded assessment dossier.")
    report.add_argument(
        "--verdict",
        metavar="PATH",
        help="The machine-readable judgement (adds the ceiling and ranking).",
    )
    report.add_argument("--hunt", metavar="PATH", help="The hunt plan.")
    report.add_argument("--product", metavar="PATH", help="The product JSON.")
    report.add_argument("--bundle", metavar="PATH", help="The STIX bundle.")
    report.add_argument(
        "--require-complete",
        action="store_true",
        help="Refuse (exit 1) when a link of the chain is missing.",
    )
    report.add_argument("-o", "--output", metavar="PATH", help="Write here instead of standard output.")

    chain = sub.add_parser("chain", help="Run the seven steps over a directory of artifacts.")
    chain.add_argument("--dir", default="demo", metavar="PATH", help="Directory with the four inputs.")
    chain.add_argument("--out", metavar="PATH", help="Output directory (default: <dir>/out).")
    chain.add_argument(
        "--force",
        action="store_true",
        help="Allow --out to replace a non-empty directory.",
    )
    chain.add_argument("--json", action="store_true", dest="as_json", help="Machine-readable summary.")
    return parser


def _run_report(args: argparse.Namespace) -> int:
    documents = {
        "pir": read_json(args.pir) if args.pir else None,
        "assessment": read_json(args.assessment) if args.assessment else None,
        "verdict": read_json(args.verdict) if args.verdict else None,
        "hunt": read_json(args.hunt) if args.hunt else None,
        "product": read_json(args.product) if args.product else None,
        "bundle": read_json(args.bundle) if args.bundle else None,
    }
    for name, document in documents.items():
        if document is not None and not isinstance(document, dict):
            raise CannotCheck(f"the {name} file is not a JSON object")

    combined = dict(documents["assessment"] or {})
    combined.update(documents["verdict"] or {})
    marking = None
    if documents["bundle"]:
        label = effective_marking(documents["bundle"])
        marking = f"TLP:{label}" if label else None
    elif documents["product"]:
        tlp = str(documents["product"].get("tlp") or "").upper()
        marking = f"TLP:{tlp}" if tlp else None

    missing = missing_artifacts(
        pir=documents["pir"],
        assessment=combined or None,
        hunt=documents["hunt"],
        product=documents["product"] or documents["bundle"],
    )

    text = render_report(
        pir=documents["pir"],
        assessment=combined or None,
        hunt=documents["hunt"],
        product=documents["product"],
        bundle=documents["bundle"],
        marking=marking,
    )
    if args.output:
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        print(f"ctisuite: report -> {args.output}")
    else:
        print(text, end="")

    if args.require_complete and missing:
        print(f"ctisuite: the chain is incomplete: {', '.join(missing)}", file=sys.stderr)
        return FINDING
    return OK


def _run_chain(args: argparse.Namespace) -> int:
    from cti_suite.chain import run_chain

    summary = run_chain(args.dir, out=args.out, force=args.force)
    if args.as_json:
        emit(summary)
    else:
        for index, step in enumerate(summary["steps"], start=1):
            total = len(summary["steps"])
            print(f"== {index}/{total}  {step['step']}")
            for key, value in step["summary"].items():
                print(f"   {key:12s}: {value}")
            print(f"   status      : {step['status']}")
            if step["status"] != 0:
                break
        if summary["status"] == 0:
            print(f"\nOK — the chain ran and the product is {summary['report']}")
    return summary["status"]


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    def body() -> int:
        if args.command == "chain":
            return _run_chain(args)
        return _run_report(args)

    if args.command == "chain":
        try:
            return body()
        except (FileNotFoundError, CannotCheck) as exc:
            print(f"cannot check: {exc}", file=sys.stderr)
            return CANNOT_CHECK
    return run(body)


if __name__ == "__main__":
    raise SystemExit(main())
