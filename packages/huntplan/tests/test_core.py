"""Tests for the hunting method."""

from __future__ import annotations

from huntplan.core import assess_hunt_maturity, build_hunt_plan, data_sources_for, hmm_levels, validate_hypothesis


def test_hmm_has_five_levels() -> None:
    levels = hmm_levels()
    assert [level["level"] for level in levels] == [0, 1, 2, 3, 4]
    assert levels[4]["name"] == "Leading"


def test_a_good_hypothesis_is_falsifiable() -> None:
    result = validate_hypothesis(
        "If the actor uses scheduled tasks, then process creation logs will show schtasks.exe with a /create argument"
    )
    assert result["falsifiable"] is True
    assert result["findings"] == []


def test_a_non_falsifiable_hypothesis_is_high() -> None:
    result = validate_hypothesis("The actor is probably active somewhere")
    codes = [finding["code"] for finding in result["findings"]]
    assert "not-falsifiable" in codes
    assert result["falsifiable"] is False


def test_hedging_and_vagueness_are_flagged() -> None:
    result = validate_hypothesis("It might be something")
    codes = [finding["code"] for finding in result["findings"]]
    assert "hedged" in codes
    assert "too-vague" in codes


def test_data_sources_for_known_and_unknown() -> None:
    known = data_sources_for("t1059")
    assert known["known"] is True
    assert known["technique_id"] == "T1059"
    assert data_sources_for("T9999")["known"] is False


def test_maturity_ladder_requires_each_rung() -> None:
    assert assess_hunt_maturity({})["level"] == 0
    assert assess_hunt_maturity({"structured_data": True})["level"] == 1
    assert assess_hunt_maturity({"documented_procedures": True})["level"] == 0  # prerequisite missing
    full = assess_hunt_maturity(
        {
            "structured_data": True,
            "documented_procedures": True,
            "analyst_hypotheses": True,
            "automated_detection": True,
        }
    )
    assert full["level"] == 4
    assert full["gaps"] == []


def test_a_complete_plan_is_ready() -> None:
    plan = build_hunt_plan(
        question="Has actor X moved laterally?",
        hypothesis="If actor X moves laterally, then authentication logs will show NTLM logons to multiple hosts",
        techniques=["T1021", "T1078"],
        closure="Confirmed if two or more hosts show the pattern; refuted if no such logons exist over 30 days",
        actor="Actor X",
    )
    assert plan["ready"] is True
    assert plan["gaps"] == []
    assert any(entry["known"] for entry in plan["techniques"])


def test_an_incomplete_plan_lists_gaps() -> None:
    plan = build_hunt_plan(question="?", hypothesis="hunt for the actor", techniques=[], closure="")
    assert plan["ready"] is False
    codes = [finding["code"] for finding in plan["validation"]["findings"]]
    assert "not-falsifiable" in codes
    assert any("closure" in gap for gap in plan["gaps"])
    assert any("ATT&CK technique" in gap for gap in plan["gaps"])
