"""assessment-mcp command-line interface: grade a claim, keep the ledger, verify it."""

from __future__ import annotations

import argparse

from cti_method import schema as schema_module
from cti_method.contract import (
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
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="assessment", description="Grade any claim, and keep a ledger.")
    parser.add_argument("--version", action="version", version=f"assessment {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    grade_cmd = sub.add_parser("grade", help="Grade a claim on two axes.")
    grade_cmd.add_argument("--confidence", required=True, choices=["high", "moderate", "low"])
    grade_cmd.add_argument("--probability", default=None)

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

    ledger = sub.add_parser("ledger", help="Read a ledger of graded claims.")
    ledger.add_argument("path")
    ledger.add_argument("--verify", action="store_true", help="Verify the hash chain.")
    return parser


def _run_assess(args: argparse.Namespace) -> int:
    document = read_json(args.path)
    if not isinstance(document, dict):
        raise CannotCheck(f"{args.path} is not a JSON object")
    register = read_json(args.register) if args.register else None
    if register is not None and not isinstance(register, dict):
        raise CannotCheck(f"{args.register} is not a JSON object")

    verdict = assess(document, register=register)
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
        append_claim(args.append, verdict, now=args.now)
    return exit_code(verdict["findings"])


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "grade":
        emit(grade(args.confidence, args.probability))
        return OK

    def body() -> int:
        if args.command == "assess":
            return _run_assess(args)
        if args.verify:
            result = verify_ledger(args.path)
            emit(result)
            return OK if result["valid"] else FINDING
        emit(read_ledger(args.path))
        return OK

    return run(body)


if __name__ == "__main__":
    raise SystemExit(main())
