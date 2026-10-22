"""CLI de pir-ledger: validar un registro y leerlo."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

from pir_ledger import __version__
from pir_ledger.validate import validate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pir",
        description="PIR, EEI and indicator register: a PIR is a question tied to a decision.",
    )
    parser.add_argument("--version", action="version", version=f"pir-ledger {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    val = sub.add_parser("validate", help="Validate the register; exit 1 on a high finding.")
    val.add_argument("path")
    val.add_argument("--json", action="store_true", help="Machine-readable output.")
    val.add_argument("--today", metavar="AAAA-MM-DD", help="Reference date (to test deadlines).")

    lis = sub.add_parser("list", help="List the requirements with their decision and deadline.")
    lis.add_argument("path")
    lis.add_argument("--today", metavar="AAAA-MM-DD")
    return parser


def _cargar(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    hoy = dt.date.fromisoformat(args.today) if getattr(args, "today", None) else None
    try:
        documento = _cargar(args.path)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"could not read {args.path}: {exc}", file=sys.stderr)
        return 2

    if args.command == "list":
        hoy = hoy or dt.date.today()
        for pir in documento.get("requirements", []):
            limite = pir.get("deadline") or "no deadline"
            dias = ""
            try:
                dias = f" ({(dt.date.fromisoformat(limite) - hoy).days:+d}d)"
            except (TypeError, ValueError):
                pass
            print(f"{pir.get('id', '?'):10s} {pir.get('priority', '?'):7s} {limite}{dias:8s} "
                  f"{pir.get('status', 'open'):9s} {pir.get('decision', '')[:60]}")
        return 0

    resultado = validate(documento, hoy)
    if args.json:
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
    else:
        for h in resultado["findings"]:
            marca = "HIGH " if h["severity"] == "high" else "med"
            print(f"  {marca} {h['code']:20s} {h['where']:24s} {h['message']}")
        print(f"\nRequirements: {resultado['requirements']}   HIGH: {resultado['high']}   MED: {resultado['medium']}")
        print("Result:", "valid" if resultado["valid"] else "NOT valid")
    return 0 if resultado["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
