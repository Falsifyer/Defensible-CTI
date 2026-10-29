"""stixforge command line: build a bundle, validate one, and verify the trace it carries."""

from __future__ import annotations

import argparse
import json
import sys

from cti_method.contract import (
    CANNOT_CHECK,
    FINDING,
    OK,
    CannotCheck,
    emit,
    finding,
    has_high,
    read_json,
    run,
)
from cti_method.trace import link, link_requirement

from stixforge import __version__
from stixforge.build import build
from stixforge.validate import external, validate

_SEV_LABEL = {"high": "HIGH ", "medium": "med  ", "low": "low  ", "info": "info "}
_MARKS = {"high": "HIGH ", "medium": "med  ", "info": "info ", "low": "low  "}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stixforge",
        description="Build STIX 2.1 bundles from an intelligence product, with provenance and a TLP marking.",
    )
    parser.add_argument("--version", action="version", version=f"stix-forge {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    build_cmd = sub.add_parser("build", help="Build the bundle from a product JSON file.")
    build_cmd.add_argument("product")
    build_cmd.add_argument("-o", "--output", help="Write the bundle here instead of standard output.")
    build_cmd.add_argument("--requirement", metavar="PATH", help="The PIR register this product answers.")
    build_cmd.add_argument("--assessment", metavar="PATH", help="The graded assessment this product is built on.")
    build_cmd.add_argument("--hunt", metavar="PATH", help="The hunt plan this product came from.")
    build_cmd.add_argument("--json", action="store_true", dest="as_json", help="Machine-readable output.")

    val = sub.add_parser("validate", help="Validate a bundle; exit 1 on a high finding, 2 if not checked.")
    val.add_argument("path")
    val.add_argument("--external", action="store_true", help="Also run stix2-validator if it is installed.")
    val.add_argument("--today", metavar="AAAA-MM-DD", help="Check indicator expiry against this date.")
    val.add_argument("--json", action="store_true", dest="as_json", help="Machine-readable output.")
    return parser


def _link(product: dict, upstream: dict, field_name: str, label: str, kind: str) -> dict:
    return link(product, field_name, upstream, label=label, kind=kind)


def _run_build(args: argparse.Namespace) -> int:
    product = read_json(args.product)
    if not isinstance(product, dict):
        raise CannotCheck(f"{args.product} is not a JSON object")

    trace: dict[str, str | None] = {
        "pir": product.get("requirement_id"),
        "assessment": product.get("assessment_id"),
        "hunt": product.get("hunt_id"),
    }
    findings: list[dict] = []
    trace_hashes: dict[str, str | None] = {}
    for path, field_name, label, kind in (
        (args.requirement, "requirement_id", "requirement register", "pir"),
        (args.assessment, "assessment_id", "assessment", "assessment"),
        (args.hunt, "hunt_id", "hunt plan", "hunt"),
    ):
        if not path:
            continue
        upstream = read_json(path)
        if not isinstance(upstream, dict):
            raise CannotCheck(f"{path} is not a JSON object")
        if kind == "pir":
            requirement = link_requirement(product, upstream)
            resolved, link_findings = requirement["id"], requirement["findings"]
            digest = requirement.get("hash")
        else:
            linked = _link(product, upstream, field_name, label, kind)
            resolved, link_findings, digest = linked["id"], linked["findings"], linked.get("hash")
        trace[kind] = resolved
        trace_hashes[kind] = digest
        findings.extend(link_findings)

    if has_high(findings):
        payload = {"built": False, "trace": trace, "findings": findings}
        if args.as_json:
            emit(payload)
        else:
            for item in findings:
                print(f"  {_SEV_LABEL.get(item['severity'], item['severity'])} {item['code']}: {item['message']}",
                      file=sys.stderr)
        return FINDING

    try:
        bundle = build(product, trace=trace, trace_hashes=trace_hashes)
    except ValueError as exc:
        findings.append(finding("product-invalid", "high", str(exc)))
        if args.as_json:
            emit({"built": False, "findings": findings})
        else:
            print(f"stixforge: {exc}", file=sys.stderr)
        return FINDING

    # The factory does not write what its own validator would reject.
    check = validate(bundle)
    if not check.get("checked", True):
        raise CannotCheck(f"the bundle is too large to check: {check['findings'][0]['message']}")
    if not check["valid"]:
        payload = {"built": False, "findings": check["findings"]}
        if args.as_json:
            emit(payload)
        else:
            for item in check["findings"]:
                if item["severity"] == "high":
                    print(f"  HIGH  {item['code']}: {item['message']}", file=sys.stderr)
        return FINDING

    if args.output:
        from pathlib import Path

        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json.dumps(bundle, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if args.as_json:
            emit({"built": True, "path": args.output, "objects": len(bundle["objects"]), "trace": trace})
        else:
            print(f"stixforge: {len(bundle['objects'])} objects -> {args.output}")
    else:
        emit(bundle)
    return OK


def _run_validate(args: argparse.Namespace) -> int:
    bundle = read_json(args.path)
    result = validate(bundle, today=args.today)
    schema_checked = False
    if args.external:
        external_check = external(bundle, args.path)
        result["external"] = external_check
        if not external_check.get("available"):
            print("stixforge: neither stix2 nor stix2-validator is installed; the external "
                  "check was NOT run", file=sys.stderr)
        else:
            schema = external_check.get("schema")
            if schema and schema.get("checked"):
                schema_checked = True
                if not schema.get("ok"):
                    result["valid"] = False
                    detail = "; ".join(schema.get("errors") or ["unknown schema error"])
                    result["findings"].append({
                        "code": "external-schema", "severity": "high", "where": schema["tool"],
                        "message": f"the OASIS JSON schemas rejected the bundle: {detail}",
                    })
            library = external_check.get("library")
            if library and not library["ok"]:
                result["valid"] = False
                result["findings"].append({
                    "code": "external-library", "severity": "high", "where": library["tool"],
                    "message": f"the OASIS library rejected the bundle: {library['error']}",
                })
            validator = external_check.get("validator")
            if validator:
                no_schemas = "Cannot locate a schema" in validator["output"]
                if validator["code"] == 0:
                    schema_checked = True
                elif validator["code"] == 2 and no_schemas:
                    # The bundle is not necessarily wrong: the validator has no schema
                    # cache (it downloads it). "Not checked" is neither "invalid" nor "clean".
                    result["findings"].append({
                        "code": "external-not-checked", "severity": "info", "where": validator["tool"],
                        "message": "could not validate: the validator has no schema cache",
                    })
                else:
                    result["valid"] = False
                    result["findings"].append({
                        "code": "external-validator", "severity": "high", "where": validator["tool"],
                        "message": f"the external validator rejected the bundle (exit {validator['code']})",
                    })
        result["external"]["schema_checked"] = schema_checked

    if args.as_json:
        emit(result)
    else:
        for item in result["findings"]:
            label = _MARKS.get(item["severity"], item["severity"])
            print(f"  {label} {item['code']:26s} {item.get('where', ''):46s} {item['message']}")
        external_output = result.get("external")
        if external_output:
            if not external_output.get("available"):
                print("\nExternal: nothing installed")
            else:
                schema = external_output.get("schema")
                if schema:
                    print(f"\nExternal (schema): {schema['tool']} -> "
                          f"{'OK' if schema.get('ok') else 'REJECTED'}")
                library = external_output.get("library")
                if library:
                    print(f"\nExternal (library): {library['tool']} -> "
                          f"{'OK' if library['ok'] else 'REJECTED'}")
                validator = external_output.get("validator")
                if validator:
                    print(f"External (validator): {validator['tool']} -> exit {validator['code']}")
        print(f"\nObjects: {result['objects']}   HIGH: {result['high']}   MED: {result['medium']}")
        print("Result:", "valid" if result["valid"] else "NOT valid")

    if args.external:
        external_result = result.get("external", {})
        if not external_result.get("available", False):
            return CANNOT_CHECK
        if result["valid"] and not external_result.get("schema_checked", False):
            print(
                "stixforge: external schema validation was NOT checked "
                "(the OASIS library parse is not a schema validation)",
                file=sys.stderr,
            )
            return CANNOT_CHECK
    return OK if result["valid"] else FINDING


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    def body() -> int:
        if args.command == "build":
            return _run_build(args)
        return _run_validate(args)

    return run(body)


if __name__ == "__main__":
    raise SystemExit(main())
