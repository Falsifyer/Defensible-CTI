"""Tests for the CLI and MCP tools."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from assessment.cli import main


def _claim(**overrides) -> dict:
    document = {
        "id": "claim-001",
        "question": "Is the claim supported?",
        "hypotheses": ["a", "b"],
        "evidence": [
            {
                "id": "E1",
                "statement": "x",
                "source": "telemetry",
                "type": "infrastructure",
                "consistency": {"a": "C", "b": "I"},
            }
        ],
        "judgement": {"confidence": "moderate"},
    }
    document.update(overrides)
    return document


def test_grade_command(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["grade", "--confidence", "high"]) == 0
    assert json.loads(capsys.readouterr().out)["confidence"] == "high"


def test_ledger_command(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["ledger", str(tmp_path / "none.jsonl")]) == 0
    assert json.loads(capsys.readouterr().out)["count"] == 0


def test_assess_command(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "claim.json"
    path.write_text(json.dumps(_claim()), encoding="utf-8")
    assert main(["assess", str(path)]) == 0
    assert json.loads(capsys.readouterr().out)["ranking"] == ["a", "b"]


def test_strict_accepts_the_verdict_it_just_emitted(tmp_path: Path) -> None:
    """A1: --strict must not fail on the tool's own valid output."""
    path = tmp_path / "claim.json"
    path.write_text(json.dumps(_claim()), encoding="utf-8")
    assert main(["assess", str(path), "--strict"]) == 0


def test_assess_refuses_a_grade_the_evidence_cannot_support(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "claim.json"
    path.write_text(json.dumps(_claim(judgement={"confidence": "high"})), encoding="utf-8")
    assert main(["assess", str(path)]) == 1
    assert "grade-exceeds-evidence" in {item["code"] for item in json.loads(capsys.readouterr().out)["findings"]}


def test_assess_refuses_a_claim_with_no_grade(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "claim.json"
    path.write_text(json.dumps(_claim(judgement=None)), encoding="utf-8")
    assert main(["assess", str(path)]) == 1
    assert "no-grade" in {item["code"] for item in json.loads(capsys.readouterr().out)["findings"]}


def test_assess_verifies_the_chain_against_the_previous_judgement(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    claim = tmp_path / "claim.json"
    claim.write_text(json.dumps(_claim()), encoding="utf-8")
    previous = tmp_path / "judgement.json"
    previous.write_text(json.dumps({"hypotheses_favoured": ["b", "a"], "ceiling": "moderate"}), encoding="utf-8")
    assert main(["assess", str(claim), "--against", str(previous)]) == 1
    out = json.loads(capsys.readouterr().out)
    assert out["reproduced"] is False


def test_assess_checks_the_requirement_against_the_register(tmp_path: Path) -> None:
    claim = tmp_path / "claim.json"
    claim.write_text(json.dumps(_claim(requirement_id="PIR-999")), encoding="utf-8")
    register = tmp_path / "pir.json"
    register.write_text(json.dumps({"id": "PIR-2026-Q4", "requirements": [{"id": "PIR-001"}]}), encoding="utf-8")
    assert main(["assess", str(claim), "--register", str(register)]) == 1


def test_ledger_verify_command(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    from assessment.core import append_claim

    path = tmp_path / "ledger.jsonl"
    append_claim(str(path), {"id": "c1"})
    assert main(["ledger", str(path), "--verify", "--no-anchor"]) == 0
    assert json.loads(capsys.readouterr().out)["valid"] is True


def test_a_bare_verify_is_not_clean(tmp_path: Path) -> None:
    from assessment.core import append_claim

    path = tmp_path / "ledger.jsonl"
    append_claim(str(path), {"id": "c1"})
    assert main(["ledger", str(path), "--verify"]) == 2


def test_ledger_head_file_detects_a_truncated_tail(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "claim.json"
    path.write_text(json.dumps(_claim()), encoding="utf-8")
    ledger = tmp_path / "ledger.jsonl"
    head = tmp_path / "ledger.head"
    for _ in range(2):
        assert (
            main(
                [
                    "assess",
                    str(path),
                    "--append",
                    str(ledger),
                    "--head-out",
                    str(head),
                    "--now",
                    "2026-10-22T00:00:00Z",
                ]
            )
            == 0
        )
    capsys.readouterr()
    assert main(["ledger", str(ledger), "--verify", "--head-file", str(head)]) == 0

    lines = ledger.read_text(encoding="utf-8").splitlines()
    ledger.write_text(lines[0] + "\n", encoding="utf-8")
    assert main(["ledger", str(ledger), "--verify", "--head-file", str(head)]) == 1


def test_cli_returns_two_when_the_file_cannot_be_read(tmp_path: Path) -> None:
    assert main(["assess", str(tmp_path / "missing.json")]) == 2
    assert main(["ledger", str(tmp_path / "missing.jsonl"), "--verify", "--no-anchor"]) == 1


def test_cli_returns_two_for_a_structurally_invalid_claim(tmp_path: Path) -> None:
    """A6: malformed content is 'could not check' (2), never a refusal (1)."""
    bad_type = {**_claim(), "evidence": [{**_claim()["evidence"][0], "type": "not-a-type"}]}
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(bad_type), encoding="utf-8")
    assert main(["assess", str(path)]) == 2

    bad_grade = {**_claim(), "judgement": {"confidence": "certain"}}
    path.write_text(json.dumps(bad_grade), encoding="utf-8")
    assert main(["assess", str(path)]) == 2


def test_mcp_tools() -> None:
    pytest.importorskip("mcp")
    from assessment import mcp_server

    assert mcp_server.grade_claim("high")["confidence"] == "high"
    assert "ranking" in mcp_server.weigh_evidence(
        [{"id": "E1", "statement": "x", "source": "s", "type": "infrastructure", "consistency": {"a": "C"}}],
        ["a", "b"],
    )
    ceiling = mcp_server.grade_ceiling(
        [{"id": "E1", "statement": "x", "source": "s", "type": "infrastructure", "consistency": {"a": "C", "b": "I"}}]
    )
    assert ceiling["ceiling"] == "moderate"
