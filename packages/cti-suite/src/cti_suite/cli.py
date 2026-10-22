"""ctisuite command line: one report from the artifacts the cycle produced."""

from __future__ import annotations

import argparse
from pathlib import Path

from cti_method.contract import OK, CannotCheck, read_json, run
from cti_method.stix import effective_marking

from cti_suite import __version__
from cti_suite.report import render_report


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
    report.add_argument("-o", "--output", metavar="PATH", help="Write here instead of standard output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    def body() -> int:
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
        return OK

    return run(body)


if __name__ == "__main__":
    raise SystemExit(main())
