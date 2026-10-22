"""The cycle as one command, with no shell in between."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cti_suite.chain import run_chain
from cti_suite.cli import main

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def chain(tmp_path_factory: pytest.TempPathFactory) -> dict:
    out = tmp_path_factory.mktemp("chain")
    summary = run_chain(ROOT / "demo", out=out)
    assert summary["status"] == 0, summary
    return summary


def test_the_chain_runs_all_eight_steps(chain: dict) -> None:
    steps = [item["step"] for item in chain["steps"]]
    assert steps == [
        "pir validate",
        "cryptonym assess",
        "assessment assess",
        "assessment ledger --verify",
        "huntplan validate",
        "stixforge build",
        "sharegate check",
        "ctisuite report",
    ]


def test_the_chain_writes_the_files_the_next_step_reads(chain: dict) -> None:
    out = Path(chain["out"])
    files = (
        "pir.json", "judgement.json", "verdict.json", "ledger.jsonl",
        "hunt.json", "bundle.json", "gate.json", "product.md",
    )
    for name in files:
        assert (out / name).is_file(), name


def test_the_report_is_complete(chain: dict) -> None:
    text = Path(chain["report"]).read_text(encoding="utf-8")
    assert "## Bottom line" in text
    assert "the evidence supports at most" in text
    assert "does not contain" not in text


def test_a_broken_chain_stops_at_the_first_refusal(tmp_path: Path) -> None:
    demo = ROOT / "demo"
    for name in ("pir.json", "assessment.json", "hunt.json", "product.json"):
        (tmp_path / name).write_text((demo / name).read_text(encoding="utf-8"), encoding="utf-8")
    product = json.loads((tmp_path / "product.json").read_text(encoding="utf-8"))
    product.pop("created")
    (tmp_path / "product.json").write_text(json.dumps(product), encoding="utf-8")

    summary = run_chain(tmp_path, out=tmp_path / "out")
    assert summary["status"] == 1
    assert summary["steps"][-1]["step"] == "stixforge build"
    assert summary["report"] is None


def test_the_chain_refuses_a_directory_with_missing_inputs(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="missing"):
        run_chain(tmp_path)


def test_chain_json_is_machine_readable(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    out = tmp_path / "out"
    code = main(["chain", "--dir", str(ROOT / "demo"), "--out", str(out), "--json"])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == 0
    assert payload["report"].endswith("product.md")
