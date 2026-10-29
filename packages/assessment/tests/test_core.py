"""Tests for the ledger engine and the derived grade."""

from __future__ import annotations

import json
from pathlib import Path

from assessment.core import (
    append_claim,
    assess,
    calibrate,
    check_against,
    filter_truth,
    grade,
    ledger_head,
    method_documentation,
    read_ledger,
    verify_ledger,
    weigh,
    write_head,
)


def _evidence(evidence_id: str, source: str, kind: str, a: str, b: str) -> dict:
    return {
        "id": evidence_id,
        "statement": f"item {evidence_id}",
        "source": source,
        "type": kind,
        "consistency": {"a": a, "b": b},
    }


def test_grade_carries_two_independent_axes() -> None:
    result = grade("low", "very_likely")
    assert result["two_axis"] is True
    assert result["confidence"] == "low"
    assert result["probability"] == "very_likely"


def test_a_probability_can_name_its_proposition() -> None:
    result = grade("low", "very_likely", "the actor is the same")
    assert result["probability_of"] == "the actor is the same"
    assert "that the actor is the same is true" in result["label"]


def test_weigh_accepts_arbitrary_hypothesis_labels() -> None:
    evidence = [
        {
            "id": "E1",
            "statement": "the actor used a unique implant",
            "source": "reporting",
            "type": "code",
            "consistency": {"compromise": "C", "false-alarm": "I"},
        }
    ]
    result = weigh(evidence, ["false-alarm", "compromise"])
    assert result["ranking"] == ["compromise", "false-alarm"]
    assert result["inconsistencies"] == {"false-alarm": 1, "compromise": 0}
    assert result["matrix"]["E1"]["compromise"] == "C"


def test_a_tie_is_not_resolved_by_hypothesis_order() -> None:
    """A2: the same evidence must not change its bottom line when the labels are reordered."""
    document = {
        "question": "same actor?",
        "hypotheses": ["a", "b"],
        "evidence": [
            _evidence("E1", "source A", "infrastructure", "I", "C"),
            _evidence("E2", "source B", "infrastructure", "C", "I"),
        ],
        "judgement": {"confidence": "low"},
    }
    first = assess(document)
    second = assess({**document, "hypotheses": ["b", "a"]})
    assert first["favoured"] is None
    assert set(first["tied"]) == {"a", "b"}
    assert second["favoured"] is None
    assert set(second["tied"]) == {"a", "b"}
    assert first["ceiling"] == second["ceiling"]


def test_restating_one_source_does_not_flip_the_ranking() -> None:
    """A3: the ACH ranking counts voices, not items."""
    document = {
        "question": "same actor?",
        "hypotheses": ["a", "b"],
        "evidence": [
            _evidence("E1", "source A", "infrastructure", "I", "C"),
            _evidence("E2", "source B", "infrastructure", "C", "I"),
            _evidence("E1b", "source A", "infrastructure", "I", "C"),
        ],
        "judgement": {"confidence": "low"},
    }
    verdict = assess(document)
    assert set(verdict["tied"]) == {"a", "b"}
    assert verdict["inconsistency_scores"] == {"a": 0.5, "b": 0.5}


def test_weigh_needs_at_least_two_hypotheses() -> None:
    import pytest

    with pytest.raises(ValueError, match="two competing hypotheses"):
        weigh([], ["only-one"])


def test_filter_truth_requires_independent_sources() -> None:
    adjudication = {
        "truth": "same_actor",
        "standard": "vendor-consensus",
        "sources": [
            {"publisher": "A", "url": "https://a", "category": "vendor", "kind": "asserts-same"},
            {"publisher": "B", "url": "https://b", "category": "vendor", "kind": "asserts-same"},
        ],
    }
    verdict = filter_truth(adjudication)
    assert verdict["admissible"] is True
    assert verdict["effective_truth"] == "same_actor"


def test_assess_combines_ach_grading_and_adjudication() -> None:
    document = {
        "question": "Did actor X compromise host Y?",
        "hypotheses": ["compromise", "benign"],
        "evidence": [
            _evidence("E1", "telemetry A", "code", "C", "I"),
            _evidence("E2", "telemetry B", "infrastructure", "C", "I"),
        ],
        "judgement": {"confidence": "high", "probability": "very_likely"},
        "adjudication": {
            "truth": "distinct",
            "standard": "independent-corroboration",
            "sources": [
                {"publisher": "A", "url": "https://a", "category": "community", "kind": "asserts-distinct"},
                {"publisher": "B", "url": "https://b", "category": "vendor", "kind": "asserts-distinct"},
            ],
        },
    }
    verdict = assess(document)
    assert verdict["ranking"][0] == "compromise"
    assert verdict["grade"]["confidence"] == "high"
    assert verdict["ceiling"] == "high"
    assert verdict["grade_supported"] is True
    assert verdict["truth"]["admissible"] is True


def test_a_grade_above_the_evidence_is_refused() -> None:
    document = {
        "question": "same actor?",
        "hypotheses": ["a", "b"],
        "evidence": [_evidence("E1", "one source", "code", "C", "I")],
        "judgement": {"confidence": "high"},
    }
    verdict = assess(document)
    assert verdict["ceiling"] == "moderate"
    assert verdict["grade_supported"] is False
    assert [item["code"] for item in verdict["findings"]] == ["grade-exceeds-evidence"]


def test_shared_tradecraft_cannot_carry_more_than_low() -> None:
    document = {
        "question": "same actor?",
        "hypotheses": ["a", "b"],
        "evidence": [_evidence("E1", "vendor", "tactics", "C", "I"), _evidence("E2", "vendor", "tactics", "C", "I")],
        "judgement": {"confidence": "moderate"},
    }
    verdict = assess(document)
    assert verdict["ceiling"] == "low"
    assert verdict["findings"][0]["code"] == "grade-exceeds-evidence"


def test_a_claim_without_a_grade_is_refused_not_defaulted() -> None:
    document = {
        "question": "same actor?",
        "hypotheses": ["a", "b"],
        "evidence": [_evidence("E1", "s", "code", "C", "I")],
    }
    verdict = assess(document)
    assert verdict["grade"]["confidence"] is None
    assert verdict["findings"][0]["code"] == "no-grade"


def test_a_claim_with_no_hypothesis_is_refused() -> None:
    verdict = assess(
        {
            "question": "same actor?",
            "hypotheses": [],
            "evidence": [_evidence("E1", "s", "code", "C", "I")],
            "judgement": {"confidence": "low"},
        }
    )
    assert "no-claim" in [item["code"] for item in verdict["findings"]]
    assert verdict["mode"] == "claim"


def test_a_claim_with_one_hypothesis_is_graded_as_a_claim() -> None:
    verdict = assess(
        {
            "question": "does the actor target utilities?",
            "hypotheses": ["it does"],
            "evidence": [
                {
                    "id": "E1",
                    "statement": "one documentary source",
                    "source": "cisa",
                    "type": "open_source",
                    "direct": True,
                }
            ],
            "judgement": {"confidence": "moderate"},
        }
    )
    assert verdict["mode"] == "claim"
    assert verdict["ceiling"] == "moderate"
    assert verdict["grade_supported"] is True


def test_check_against_detects_a_changed_dossier() -> None:
    document = {
        "question": "same actor?",
        "hypotheses": ["a", "b"],
        "evidence": [_evidence("E1", "s", "code", "C", "I")],
        "judgement": {"confidence": "low"},
    }
    verdict = assess(document)
    changed = check_against(verdict, {"hypotheses_favoured": ["a", "b"], "ceiling": "high"})
    assert changed[0]["code"] == "judgement-mismatch"
    assert check_against(verdict, {"hypotheses_favoured": ["a", "b"], "ceiling": "moderate"}) == []


def test_calibrate_scores_labelled_calls() -> None:
    summary = calibrate(
        [
            {"id": "c1", "called": True, "truth": True, "confidence": "high"},
            {"id": "c2", "called": True, "truth": False, "confidence": "high"},
        ]
    )
    assert summary["metrics"]["total"] == 2
    assert summary["metrics"]["false_merge_rate"] == 1.0
    assert summary["calibration"]["high"]["accuracy"] == 0.5


def test_the_ledger_is_a_hash_chain(tmp_path: Path) -> None:
    path = tmp_path / "ledger" / "claims.jsonl"
    append_claim(str(path), {"id": "c1", "confidence": "moderate"})
    append_claim(str(path), {"id": "c2", "confidence": "high"})

    result = read_ledger(str(path))
    assert result["count"] == 2
    assert result["claims"][1]["id"] == "c2"
    assert result["entries"][0]["prev_hash"] == "0" * 64
    assert result["entries"][1]["prev_hash"] == result["entries"][0]["hash"]
    assert verify_ledger(str(path))["valid"] is True


def test_a_tampered_ledger_line_is_detected(tmp_path: Path) -> None:
    path = tmp_path / "claims.jsonl"
    append_claim(str(path), {"id": "c1", "confidence": "moderate"})
    append_claim(str(path), {"id": "c2", "confidence": "high"})

    lines = path.read_text(encoding="utf-8").splitlines()
    entry = json.loads(lines[0])
    entry["claim"]["confidence"] = "high"  # silent upgrade of a judgement
    lines[0] = json.dumps(entry)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    result = verify_ledger(str(path))
    assert result["valid"] is False
    assert result["broken_at"] == 1


def test_tail_truncation_needs_an_anchor(tmp_path: Path) -> None:
    """A5: the prefix is a valid chain; only a head/length anchor sees the missing tail."""
    path = tmp_path / "claims.jsonl"
    manifest = tmp_path / "claims.head"
    append_claim(str(path), {"id": "c1"}, head_out=str(manifest))
    append_claim(str(path), {"id": "c2"}, head_out=str(manifest))
    anchor = ledger_head(str(path))
    assert anchor["entries"] == 2

    lines = path.read_text(encoding="utf-8").splitlines()
    path.write_text(lines[0] + "\n", encoding="utf-8")

    # Without an anchor the remaining prefix is indistinguishable from a complete ledger.
    assert verify_ledger(str(path))["valid"] is True
    anchored = verify_ledger(
        str(path), expected_head=anchor["head"], expected_count=anchor["entries"]
    )
    assert anchored["valid"] is False
    assert "anchor" in anchored["reason"] or "entries" in anchored["reason"]
    from_manifest = verify_ledger(str(path), head_file=str(manifest))
    assert from_manifest["valid"] is False


def test_write_head_records_the_current_head(tmp_path: Path) -> None:
    path = tmp_path / "claims.jsonl"
    append_claim(str(path), {"id": "c1"})
    manifest = tmp_path / "claims.head"
    head = write_head(str(path), str(manifest))
    assert json.loads(manifest.read_text(encoding="utf-8"))["head"] == head["head"]
    assert head["entries"] == 1


def test_reading_a_missing_ledger_is_empty(tmp_path: Path) -> None:
    result = read_ledger(str(tmp_path / "none.jsonl"))
    assert result["count"] == 0
    assert result["claims"] == []


def test_method_documentation_is_available_from_the_installed_package() -> None:
    result = method_documentation("method")
    assert "shared core" in result["content"] or "ceiling" in result["content"]


def test_a_ledger_entry_can_be_written_at_a_fixed_instant(tmp_path: Path) -> None:
    path = tmp_path / "fixed.jsonl"
    append_claim(str(path), {"id": "c1"}, now="2026-10-22T00:00:00Z")
    append_claim(str(path), {"id": "c2"}, now="2026-10-22T00:00:00Z")
    entries = read_ledger(str(path))["entries"]
    assert [entry["created_at"] for entry in entries] == ["2026-10-22T00:00:00Z", "2026-10-22T00:00:00Z"]
    assert entries[1]["prev_hash"] == entries[0]["hash"]
    assert verify_ledger(str(path))["valid"] is True


def test_a_bad_fixed_instant_is_refused(tmp_path: Path) -> None:
    import pytest

    with pytest.raises(ValueError, match="ISO 8601"):
        append_claim(str(tmp_path / "bad.jsonl"), {"id": "c1"}, now="yesterday")
