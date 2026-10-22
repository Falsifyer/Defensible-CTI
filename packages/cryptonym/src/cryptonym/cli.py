"""Cryptonym command-line interface.

``snapshot`` captures a source; ``ingest`` normalises names from a source into
designations; ``assess`` prints the machine-readable judgement; ``render`` writes the
human product; ``export`` stages a shareable form. The core never performs a network
call unless a network mode is explicitly selected.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cti_method.contract import exit_code

from cryptonym import __version__
from cryptonym import snapshot as snapshot_module
from cryptonym.assess.grading import assess_actor_pair
from cryptonym.config import EXPORT_FORMATS, SUPPORTED_SOURCES
from cryptonym.export.markdown import render_assessment
from cryptonym.export.misp_galaxy import to_misp_galaxy_cluster
from cryptonym.export.stix_bundle import to_stix_bundle
from cryptonym.export.taxii import to_taxii_envelope
from cryptonym.model.assessment import load_assessment
from cryptonym.security import SecurityValidationError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cryptonym",
        description="Actor alias reconciliation with provenance and graded confidence.",
    )
    parser.add_argument("--version", action="version", version=f"cryptonym {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    snap = sub.add_parser("snapshot", help="Capture a source (record its bytes and hash).")
    snap.add_argument("--source", metavar="URL", help="HTTP(S) endpoint to capture.")
    snap.add_argument("--verify", metavar="PATH", help="Re-check a recorded snapshot's hash.")
    snap.add_argument("--allow-private", action="store_true", help="Permit private/loopback endpoints.")
    snap.add_argument("-o", "--output", metavar="PATH", help="Write the snapshot to a file instead of stdout.")

    ingest = sub.add_parser("ingest", help="Normalise names from a source into designations.")
    ingest.add_argument("--source", choices=SUPPORTED_SOURCES, required=True)
    source = ingest.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", metavar="PATH", help="Local JSON document to read.")
    source.add_argument("--url", metavar="URL", help="HTTP(S) document to fetch and read.")
    ingest.add_argument("--allow-private", action="store_true", help="Permit private/loopback endpoints.")
    ingest.add_argument("-o", "--output", metavar="PATH", help="Write to a file instead of stdout.")

    assess = sub.add_parser("assess", help="Print the machine-readable judgement for a dossier.")
    assess.add_argument("dossier", help="Path to an assessment JSON file.")
    assess.add_argument(
        "--strict",
        action="store_true",
        help="Validate the judgement against the published schema (needs the jsonschema extra).",
    )

    adjudicate = sub.add_parser("adjudicate", help="Run the external-truth filter over an adjudicated corpus.")
    adjudicate.add_argument("corpus", help="Path to an adjudicated corpus JSON file.")
    adjudicate.add_argument("--strict", action="store_true", help="Fail if a binary truth was not earned.")

    render = sub.add_parser("render", help="Render a dossier as a markdown product.")
    render.add_argument("dossier", help="Path to an assessment JSON file.")
    render.add_argument("-o", "--output", metavar="PATH", help="Write to a file instead of stdout.")

    export = sub.add_parser("export", help="Export a dossier (STIX / MISP / TAXII).")
    export.add_argument("dossier", help="Path to an assessment JSON file.")
    export.add_argument("--format", choices=EXPORT_FORMATS, required=True)
    export.add_argument("-o", "--output", metavar="PATH", help="Write to a file instead of stdout.")
    return parser


def _emit(text: str, output: str | None) -> None:
    if output:
        Path(output).write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
    else:
        sys.stdout.write(text if text.endswith("\n") else text + "\n")


def _run_snapshot(args: argparse.Namespace) -> int:
    if args.verify:
        recorded = snapshot_module.load(args.verify)
        verified = recorded.verify()
        print(json.dumps({"source": recorded.source, "sha256": recorded.sha256, "verified": verified}, indent=2))
        return 0 if verified else 1
    if not args.source:
        print("error: provide --source URL or --verify PATH", file=sys.stderr)
        return 2
    captured = snapshot_module.fetch(args.source, allow_private=args.allow_private)
    _emit(json.dumps(captured.to_dict(), indent=2, ensure_ascii=False), args.output)
    return 0


def _run_ingest(args: argparse.Namespace) -> int:
    from cryptonym.ingest import from_document

    if args.url:
        from cryptonym.ingest.fetch import fetch_json

        data = fetch_json(args.url, allow_private=args.allow_private)
    else:
        data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    designations = from_document(args.source, data)
    payload = [
        {"vendor": item.vendor, "name": item.name, "source_url": item.source_url, "date": item.date}
        for item in designations
    ]
    _emit(json.dumps(payload, indent=2, ensure_ascii=False), args.output)
    return 0


def _run_assess(path: str, strict: bool = False) -> int:
    assessment = load_assessment(path)
    verdict = assess_actor_pair(assessment)
    if strict:
        from cti_method import schema as schema_module

        try:
            schema_module.validate(verdict, "judgement")
        except RuntimeError as exc:
            print(f"cannot check: {exc}", file=sys.stderr)
            return 2
        except Exception as exc:  # noqa: BLE001 - any schema failure means "not checked"
            print(f"cannot check: the judgement does not match its schema: {exc}", file=sys.stderr)
            return 2
    print(json.dumps(verdict, indent=2, ensure_ascii=False))
    return exit_code(verdict["grade_findings"])


def _run_adjudicate(path: str, strict: bool) -> int:
    from cryptonym.evaluate.adjudication import validate_corpus
    from cryptonym.evaluate.metrics import evaluate_adjudicated

    document = json.loads(Path(path).read_text(encoding="utf-8"))
    problems = validate_corpus(document)
    if problems:
        for problem in problems:
            print(f"invalid corpus: {problem}", file=sys.stderr)
        return 2

    summary = evaluate_adjudicated(document)
    print(
        json.dumps(
            {
                "metrics": summary["metrics"],
                "coverage": summary["coverage"],
                "by_standard": summary["by_standard"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    if strict:
        unearned = [
            row
            for row in summary["results"]
            if row["declared_truth"] in ("same_actor", "distinct") and not row["admissible"]
        ]
        if unearned:
            for row in unearned:
                print(f"strict: {row['id']} claims {row['declared_truth']} without earning it", file=sys.stderr)
            return 1
    return 0


def _run_render(path: str, output: str | None) -> int:
    _emit(render_assessment(load_assessment(path)), output)
    return 0


def _run_export(path: str, fmt: str, output: str | None) -> int:
    assessment = load_assessment(path)
    if fmt == "stix":
        payload = to_stix_bundle(assessment)
    elif fmt == "misp":
        payload = to_misp_galaxy_cluster(assessment)
    else:
        payload = to_taxii_envelope(assessment)
    _emit(json.dumps(payload, indent=2, ensure_ascii=False), output)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "snapshot":
            return _run_snapshot(args)
        if args.command == "ingest":
            return _run_ingest(args)
        if args.command == "assess":
            return _run_assess(args.dossier, args.strict)
        if args.command == "adjudicate":
            return _run_adjudicate(args.corpus, args.strict)
        if args.command == "render":
            return _run_render(args.dossier, args.output)
        return _run_export(args.dossier, args.format, args.output)
    except (OSError, ValueError, KeyError, RuntimeError, SecurityValidationError) as exc:
        print(f"error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
