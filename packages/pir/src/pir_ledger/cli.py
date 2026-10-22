"""CLI de pir-ledger: validar un registro, listarlo y dar sus identificadores."""

from __future__ import annotations

import argparse
import datetime as dt
import sys

from cti_method.contract import CANNOT_CHECK, FINDING, OK, CannotCheck, emit, read_json

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

    ids = sub.add_parser("ids", help="Print the requirement identifiers, for the rest of the cycle.")
    ids.add_argument("path")
    return parser


def _today(value: str | None) -> dt.date | None:
    if not value:
        return None
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        raise CannotCheck(f"--today {value!r} is not an ISO date") from exc


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        documento = read_json(args.path)
        if not isinstance(documento, dict):
            raise CannotCheck(f"{args.path} is not a JSON object")
    except CannotCheck as exc:
        print(f"cannot check: {exc}", file=sys.stderr)
        return CANNOT_CHECK

    hoy = _today(getattr(args, "today", None))
    if args.command == "ids":
        emit([pir.get("id") for pir in documento.get("requirements", []) if isinstance(pir, dict)])
        return OK

    if args.command == "list":
        referencia = hoy or dt.date.today()
        for pir in documento.get("requirements", []):
            if not isinstance(pir, dict):
                continue
            limite = pir.get("deadline") or "no deadline"
            dias = ""
            try:
                dias = f" ({(dt.date.fromisoformat(limite) - referencia).days:+d}d)"
            except (TypeError, ValueError):
                pass
            print(f"{pir.get('id', '?'):10s} {pir.get('priority', '?'):7s} {limite}{dias:8s} "
                  f"{pir.get('status', 'open'):9s} {pir.get('decision', '')[:60]}")
        return OK

    resultado = validate(documento, hoy)
    if args.json:
        emit(resultado)
    else:
        for item in resultado["findings"]:
            marca = "HIGH " if item["severity"] == "high" else "med"
            print(f"  {marca} {item['code']:20s} {item.get('where', '-'):24s} {item['message']}")
        print(f"\nRequirements: {resultado['requirements']}   HIGH: {resultado['high']}   MED: {resultado['medium']}")
        print("Result:", "valid" if resultado["valid"] else "NOT valid")
    return OK if resultado["valid"] else FINDING


if __name__ == "__main__":
    raise SystemExit(main())
