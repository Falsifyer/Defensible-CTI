"""HuntPlan command-line interface."""

from __future__ import annotations

import argparse
import json

from cti_method.contract import FINDING, OK, CannotCheck, emit, finding, has_high, read_json, read_text, run
from cti_method.trace import link

from huntplan import __version__
from huntplan.core import (
    attack_provenance,
    detections_for,
    hmm_levels,
    validate_hypothesis,
    validate_plan,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="huntplan", description="Turn a question into a falsifiable hunt plan.")
    parser.add_argument("--version", action="version", version=f"huntplan {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="Check a hypothesis (text) or a plan (JSON).")
    validate.add_argument("path", help="A text file with the hypothesis, or a JSON plan.")
    validate.add_argument("--assessment", metavar="PATH", help="The assessment the plan answers; the id is verified.")
    sources = sub.add_parser("sources", help="Print the ATT&CK detection strategies for a technique.")
    sources.add_argument("technique_id", help="ATT&CK technique ID, e.g. T1059.")
    sub.add_parser("detections", help="Alias of 'sources' (ATT&CK v18 renamed data sources).")
    sub.add_parser("hmm", help="Print the Hunting Maturity Model levels.")
    return parser


def _link(plan: dict, path: str) -> list[dict]:
    upstream = read_json(path)
    if not isinstance(upstream, dict):
        raise CannotCheck(f"{path} is not a JSON object")
    return link(plan, "assessment_id", upstream, label="assessment", kind="assessment")["findings"]


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "hmm":
        emit(hmm_levels())
        return OK
    if args.command in ("sources", "detections"):
        result = detections_for(args.technique_id)
        emit(result)
        return OK if result["known"] else FINDING

    def body() -> int:
        text = read_text(args.path)
        try:
            document = json.loads(text)
        except json.JSONDecodeError:
            document = None

        if isinstance(document, dict):
            result = validate_plan(document)
            findings = list(result["validation"]["findings"])
            if args.assessment:
                for item in _link(document, args.assessment):
                    findings.append(item)
                result["validation"]["findings"] = findings
                result["ready"] = result["ready"] and not has_high(findings)
            result["attack"] = attack_provenance()
            emit(result)
            return OK if not has_high(findings) else FINDING

        result = validate_hypothesis(text)
        if args.assessment:
            result["findings"] = list(result["findings"]) + [
                finding("trace-missing", "medium", "a text hypothesis cannot cite the assessment it answers")
            ]
            result["falsifiable"] = not has_high(result["findings"])
        emit(result)
        return OK if result["falsifiable"] else FINDING

    return run(body)


if __name__ == "__main__":
    raise SystemExit(main())
