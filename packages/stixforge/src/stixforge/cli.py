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
    resultado = validate(bundle, today=args.today)
    if args.external:
        externo = external(bundle, args.path)
        resultado["external"] = externo
        if not externo.get("available"):
            print("stixforge: neither stix2 nor stix2-validator is installed; the external "
                  "check was NOT run", file=sys.stderr)
        else:
            biblioteca = externo.get("library")
            if biblioteca and not biblioteca["ok"]:
                resultado["valid"] = False
                resultado["findings"].append({
                    "code": "external-library", "severity": "high", "where": biblioteca["tool"],
                    "message": f"the OASIS library rejected the bundle: {biblioteca['error']}",
                })
            validador = externo.get("validator")
            if validador:
                sin_esquemas = "Cannot locate a schema" in validador["output"]
                if validador["code"] == 0:
                    pass
                elif validador["code"] == 2 and sin_esquemas:
                    # No es que el bundle este mal: el validador no tiene su cache de
                    # esquemas (los descarga). "No comprobado" no es "invalido" ni "limpio".
                    resultado["findings"].append({
                        "code": "external-not-checked", "severity": "info", "where": validador["tool"],
                        "message": "could not validate: the validator has no schema cache",
                    })
                else:
                    resultado["valid"] = False
                    resultado["findings"].append({
                        "code": "external-validator", "severity": "high", "where": validador["tool"],
                        "message": f"the external validator rejected the bundle (exit {validador['code']})",
                    })

    if args.as_json:
        emit(resultado)
    else:
        for item in resultado["findings"]:
            marca = _MARKS.get(item["severity"], item["severity"])
            print(f"  {marca} {item['code']:26s} {item.get('where', ''):46s} {item['message']}")
        salida_externa = resultado.get("external")
        if salida_externa:
            if not salida_externa.get("available"):
                print("\nExternal: nothing installed")
            else:
                biblioteca = salida_externa.get("library")
                if biblioteca:
                    print(f"\nExternal (library): {biblioteca['tool']} -> "
                          f"{'OK' if biblioteca['ok'] else 'REJECTED'}")
                validador = salida_externa.get("validator")
                if validador:
                    print(f"External (validator): {validador['tool']} -> exit {validador['code']}")
        print(f"\nObjects: {resultado['objects']}   HIGH: {resultado['high']}   MED: {resultado['medium']}")
        print("Result:", "valid" if resultado["valid"] else "NOT valid")

    if args.external and not resultado.get("external", {}).get("available", False):
        return CANNOT_CHECK
    return OK if resultado["valid"] else FINDING


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    def body() -> int:
        if args.command == "build":
            return _run_build(args)
        return _run_validate(args)

    return run(body)


if __name__ == "__main__":
    raise SystemExit(main())
