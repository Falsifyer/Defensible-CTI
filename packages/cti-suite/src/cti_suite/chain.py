"""The cycle as one command: seven steps, each reading what the previous one wrote.

`demo/run.sh` was the only place the whole chain existed, and a shell script is not a
product. This module runs the same steps in order, in-process, through the same entry
points the CLI exposes, and returns one exit code: the first step that refuses stops the
chain.

Nothing is reimplemented here. Each step is the real command, invoked with its real
arguments; the files it writes are the files the next step reads.
"""

from __future__ import annotations

import contextlib
import io
import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from assessment.cli import main as assessment_main
from cryptonym.cli import main as cryptonym_main
from cti_method.contract import CannotCheck
from huntplan.cli import main as huntplan_main
from pir_ledger.cli import main as pir_main
from sharegate.cli import main as sharegate_main
from stixforge.cli import main as stixforge_main

from cti_suite.cli import main as cli_main

#: Files a demo/chain directory must contain.
INPUTS = {
    "pir.json": "the PIR register",
    "assessment.json": "the graded assessment",
    "hunt.json": "the hunt plan",
    "product.json": "the product",
}


@dataclass
class Step:
    label: str
    argv: list[str]
    output: str | None = None
    capture: bool = True
    summary: dict[str, Any] = field(default_factory=dict)
    status: int = 0


def _summary(document: Any) -> dict[str, Any]:
    """The handful of values worth printing for one artifact, when the artifact has them."""
    if not isinstance(document, dict):
        return {}
    picked: dict[str, Any] = {}
    for key in ("valid", "ready", "shareable", "reproduced", "ceiling", "confidence"):
        if key in document:
            picked[key] = document[key]
    if "grade" in document and isinstance(document["grade"], dict):
        picked["declared"] = document["grade"].get("confidence")
    tied = document.get("tied") or []
    if len(tied) > 1:
        picked["favoured"] = f"{' / '.join(tied)} (tied)"
    elif "hypotheses_favoured" in document:
        picked["favoured"] = (document["hypotheses_favoured"] or [None])[0]
    if "ranking" in document and len(tied) <= 1:
        picked["favoured"] = (document["ranking"] or [None])[0]
    if "ids" in document:
        picked["requirements"] = document["ids"]
    if "effective_tlp" in document:
        picked["tlp"] = document["effective_tlp"]
    if "objects" in document:
        picked["objects"] = document["objects"]
    if "trace" in document:
        picked["trace"] = document["trace"]
    if "attack" in document and isinstance(document["attack"], dict):
        picked["attack"] = document["attack"].get("attack_version")
    if "entries" in document:
        picked["ledger_entries"] = document["entries"]
    return picked


def _trace_from_bundle(path: Path) -> dict[str, str]:
    try:
        bundle = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    report: dict[str, Any] = next(
        (obj for obj in bundle.get("objects", []) if obj.get("type") == "report"), {}
    )
    return {item["source_name"]: item["external_id"] for item in report.get("external_references", [])}


def run_chain(
    directory: str | Path,
    out: str | Path | None = None,
    *,
    clean: bool = True,
    force: bool = False,
) -> dict[str, Any]:
    """Run the seven steps over ``directory`` and return a machine-readable summary.

    ``--out`` is a destructive boundary: the target is removed before the chain runs. A
    target that is the input directory, its ancestor, the working directory, the home
    directory or the filesystem root is refused, and so is a non-empty explicit ``--out``
    without ``--force``. The implicit ``<dir>/out`` keeps its old clean-on-every-run
    behaviour.
    """
    root = Path(directory).resolve()
    missing = [name for name in INPUTS if not (root / name).is_file()]
    if missing:
        raise FileNotFoundError(f"{root} is missing: {', '.join(missing)}")
    target = Path(out).resolve() if out else root / "out"
    protected = (root, Path.cwd(), Path.home(), Path(target.anchor))
    for guarded in protected:
        if target == guarded or target in guarded.parents:
            raise CannotCheck(
                f"refusing to use {target} as --out: it contains {guarded.name or guarded}"
            )
    if target.exists() and not target.is_dir():
        raise CannotCheck(f"refusing to use {target} as --out: it is not a directory")
    if (
        clean
        and out is not None
        and target.is_dir()
        and any(target.iterdir())
        and not force
    ):
        raise CannotCheck(
            f"refusing to delete the non-empty {target}: pass --force to replace it"
        )
    if clean and target.is_dir():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)

    steps = [
        Step(
            "pir validate",
            ["pir", "validate", str(root / "pir.json"), "--json"],
            str(target / "pir-validation.json"),
        ),
        Step(
            "cryptonym assess",
            ["cryptonym", "assess", str(root / "assessment.json")],
            str(target / "judgement.json"),
        ),
        Step(
            "assessment assess",
            [
                "assessment",
                "assess",
                str(root / "assessment.json"),
                "--register",
                str(target / "pir.json"),
                "--against",
                str(target / "judgement.json"),
                "--append",
                str(target / "ledger.jsonl"),
                "--head-out",
                str(target / "ledger.head"),
            ],
            str(target / "verdict.json"),
        ),
        Step(
            "assessment ledger --verify",
            [
                "assessment",
                "ledger",
                str(target / "ledger.jsonl"),
                "--verify",
                "--head-file",
                str(target / "ledger.head"),
            ],
            str(target / "ledger-check.json"),
        ),
        Step(
            "huntplan validate",
            ["huntplan", "validate", str(root / "hunt.json"), "--assessment", str(target / "verdict.json")],
            str(target / "hunt.json"),
        ),
        Step(
            "stixforge build",
            [
                "stixforge",
                "build",
                str(root / "product.json"),
                "-o",
                str(target / "bundle.json"),
                "--requirement",
                str(target / "pir.json"),
                "--assessment",
                str(target / "verdict.json"),
                "--hunt",
                str(target / "hunt.json"),
            ],
            str(target / "bundle.json"),
            capture=False,
        ),
        Step(
            "sharegate check",
            ["sharegate", "check", str(target / "bundle.json")],
            str(target / "gate.json"),
        ),
    ]

    runners = {
        "pir": pir_main,
        "cryptonym": cryptonym_main,
        "assessment": assessment_main,
        "huntplan": huntplan_main,
        "stixforge": stixforge_main,
        "sharegate": sharegate_main,
    }

    results: list[dict[str, Any]] = []
    code = 0
    for step in steps:
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(io.StringIO()):
            step.status = runners[step.argv[0]](step.argv[1:])
        text = captured.getvalue()
        if step.output and step.capture:
            Path(step.output).write_text(text, encoding="utf-8")
            with contextlib.suppress(json.JSONDecodeError):
                step.summary = _summary(json.loads(text))
        results.append({"step": step.label, "status": step.status, "output": step.output, "summary": step.summary})
        if step.status == 0 and step.argv[0] == "pir":
            # What travels is the register that passed validation, not the original.
            shutil.copyfile(root / "pir.json", target / "pir.json")
        if step.status != 0:
            code = step.status
            break

    report_path = target / "product.md"
    if code == 0:
        report_args = [
            "report",
            "--pir", str(target / "pir.json"),
            "--assessment", str(root / "assessment.json"),
            "--verdict", str(target / "verdict.json"),
            "--hunt", str(target / "hunt.json"),
            "--product", str(root / "product.json"),
            "--bundle", str(target / "bundle.json"),
            "--require-complete",
            "-o", str(report_path),
        ]
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            report_status = cli_main(report_args)
        results.append(
            {
                "step": "ctisuite report",
                "status": report_status,
                "output": str(report_path),
                "summary": {"trace": _trace_from_bundle(target / "bundle.json")},
            }
        )
        if report_status != 0:
            code = report_status

    return {
        "directory": str(root),
        "out": str(target),
        "status": code,
        "steps": results,
        "report": str(report_path) if code == 0 else None,
    }
