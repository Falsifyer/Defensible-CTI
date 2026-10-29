"""assessment-mcp command-line interface: grade a claim, keep the ledger, verify it."""

from __future__ import annotations

import argparse
import sys

from cti_method import schema as schema_module
from cti_method.contract import (
    CANNOT_CHECK,
    FINDING,
    OK,
    CannotCheck,
    emit,
    exit_code,
    has_high,
    read_json,
    run,
)

from assessment import __version__
from assessment.core import (
    append_claim,
    assess,
    check_against,
    grade,
    read_ledger,
    verify_ledger,
    write_head,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="assessment", description="Grade any claim, and keep a ledger.")
    parser.add_argument("--version", action="version", version=f"assessment {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    grade_cmd = sub.add_parser("grade", help="Grade a claim on two axes.")
    grade_cmd.add_argument("--confidence", required=True, choices=["high", "moderate", "low"])
    grade_cmd.add_argument("--probability", default=None)
    grade_cmd.add_argument(
        "--probability-of", default=None, help="The proposition the probability is about."
    )

    assess_cmd = sub.add_parser("assess", help="Grade a full claim from a JSON document.")
    assess_cmd.add_argument("path")
    assess_cmd.add_argument("--register", metavar="PATH", help="The PIR register, to verify requirement_id.")
    assess_cmd.add_argument(
        "--against",
        metavar="PATH",
        help="The previous step's judgement, to re-derive and compare.",
    )
    assess_cmd.add_argument("--append", metavar="PATH", help="Append the verdict to this ledger.")
    assess_cmd.add_argument(
        "--strict",
        action="store_true",
        help="Validate the verdict against the published schema (needs the jsonschema extra).",
    )
    assess_cmd.add_argument(
        "--now",
        metavar="AAAA-MM-DDTHH:MM:SSZ",
        help="Fixed timestamp for the ledger entry (reproducible runs).",
    )
    assess_cmd.add_argument(
        "--head-out",
        metavar="PATH",
        help="Write a head/length manifest after appending, to anchor a later --verify.",
    )

    ledger = sub.add_parser("ledger", help="Read a ledger of graded claims.")
    ledger.add_argument("path")
    ledger.add_argument("--verify", action="store_true", help="Verify the hash chain.")
    ledger.add_argument(
        "--expect-head",
        metavar="HASH",
        help="Fail unless the ledger's final hash matches this anchor.",
    )
    ledger.add_argument(
        "--expect-count",
        type=int,
        metavar="N",
        help="Fail unless the ledger has exactly N entries.",
    )
    ledger.add_argument(
        "--head-file",
        metavar="PATH",
        help="Read the expected head and length from a manifest written by --head-out.",
    )
    ledger.add_argument(
        "--write-head",
        metavar="PATH",
        help="Write the current head/length manifest here and print it.",
    )
    ledger.add_argument(
        "--no-anchor",
        action="store_true",
        help="Explicitly verify only the internal chain; a tail truncation is not detectable.",
    )
    return parser


def _run_assess(args: argparse.Namespace) -> int:
    document = read_json(args.path)
    if not isinstance(document, dict):
        raise CannotCheck(f"{args.path} is not a JSON object")
    register = read_json(args.register) if args.register else None
    if register is not None and not isinstance(register, dict):
        raise CannotCheck(f"{args.register} is not a JSON object")

    try:
        verdict = assess(document, register=register)
    except (KeyError, TypeError, ValueError) as exc:
        raise CannotCheck(
            f"the claim is not a usable document: {type(exc).__name__}: {exc}"
        ) from exc
    if args.strict:
        try:
            schema_module.validate(verdict, "judgement")
        except RuntimeError as exc:
            raise CannotCheck(str(exc)) from exc
        except Exception as exc:  # jsonschema.ValidationError and friends
            raise CannotCheck(f"the verdict does not match its schema: {exc}") from exc
    if args.against:
        previous = read_json(args.against)
        if not isinstance(previous, dict):
            raise CannotCheck(f"{args.against} is not a JSON object")
        verdict["findings"].extend(check_against(verdict, previous))
        verdict["reproduced"] = not any(
            item["code"] == "judgement-mismatch" for item in verdict["findings"]
        )
    emit(verdict)
    if args.append and not has_high(verdict["findings"]):
        # The ledger is written but not printed: the output of `assess` is one document.
        append_claim(args.append, verdict, now=args.now, head_out=args.head_out)
    return exit_code(verdict["findings"])


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "grade":
        emit(grade(args.confidence, args.probability, args.probability_of))
        return OK

    def body() -> int:
        if args.command == "assess":
            return _run_assess(args)
        if args.write_head:
            emit(write_head(args.path, args.write_head))
            return OK
        if args.verify:
            anchored = any(
                value is not None
                for value in (args.head_file, args.expect_head, args.expect_count)
            )
            if not anchored and not args.no_anchor:
                print(
                    "cannot check: a bare --verify cannot see a truncated tail; pass "
                    "--head-file or --expect-head/--expect-count, or --no-anchor to "
                    "verify only the internal chain",
                    file=sys.stderr,
                )
                return CANNOT_CHECK
            result = verify_ledger(
                args.path,
                expected_head=args.expect_head,
                expected_count=args.expect_count,
                head_file=args.head_file,
            )
            result["anchored"] = anchored
            emit(result)
            return OK if result["valid"] else FINDING
        emit(read_ledger(args.path))
        return OK

    return run(body)


if __name__ == "__main__":
    raise SystemExit(main())
