"""stixforge command line: build a bundle and validate one."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from stixforge import __version__
from stixforge.build import build_file
from stixforge.validate import external, validate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stixforge",
        description="Build STIX 2.1 bundles from an intelligence product, with provenance and a TLP marking.",
    )
    parser.add_argument("--version", action="version", version=f"stix-forge {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="Build the bundle from a product JSON file.")
    build.add_argument("product")
    build.add_argument("-o", "--output", help="Write the bundle here instead of standard output.")

    val = sub.add_parser("validate", help="Validate a bundle; exit 1 on a high finding, 2 if not checked.")
    val.add_argument("path")
    val.add_argument("--external", action="store_true", help="Also run stix2-validator if it is installed.")
    val.add_argument("--json", action="store_true", dest="as_json", help="Machine-readable output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "build":
        try:
            bundle = build_file(args.product, args.output)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            print(f"stixforge: {exc}", file=sys.stderr)
            return 1
        if not args.output:
            print(json.dumps(bundle, indent=2, ensure_ascii=False))
        else:
            print(f"stixforge: {len(bundle['objects'])} objects -> {args.output}")
        return 0

    try:
        bundle = json.loads(Path(args.path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"stixforge: could not read {args.path}: {exc}", file=sys.stderr)
        return 2

    resultado = validate(bundle)
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
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
    else:
        for h in resultado["findings"]:
            marca = {"high": "HIGH ", "medium": "med  ", "info": "info "}[h["severity"]]
            print(f"  {marca} {h['code']:22s} {h['where']:46s} {h['message']}")
        externo = resultado.get("external")
        if externo:
            if not externo.get("available"):
                print("\nExternal: nothing installed")
            else:
                biblioteca = externo.get("library")
                if biblioteca:
                    print(f"\nExternal (library): {biblioteca['tool']} -> "
                          f"{'OK' if biblioteca['ok'] else 'REJECTED'}")
                validador = externo.get("validator")
                if validador:
                    print(f"External (validator): {validador['tool']} -> exit {validador['code']}")
        print(f"\nObjects: {resultado['objects']}   HIGH: {resultado['high']}   MED: {resultado['medium']}")
        print("Result:", "valid" if resultado["valid"] else "NOT valid")

    if args.external and not resultado.get("external", {}).get("available", False):
        return 2
    return 0 if resultado["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
