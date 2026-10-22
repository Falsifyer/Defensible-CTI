"""The shared core: the ceiling, one validator, one contract, one trace."""

from __future__ import annotations

import pytest

from cti_method.contract import CannotCheck, exit_code, finding, read_json, severity_counts
from cti_method.evidence import Consistency, Evidence, EvidenceType
from cti_method.grading import ceiling, check_declared, derived_grade
from cti_method.stix import TLP, effective_marking, marking_object, validate_bundle
from cti_method.trace import external_references, id_of, link, link_requirement


def _item(evidence_id: str, source: str, kind: EvidenceType, **consistency: Consistency) -> Evidence:
    return Evidence(
        id=evidence_id,
        statement="s",
        source=source,
        type=kind,
        consistency={key: value for key, value in consistency.items()},
    )


# ------------------------------------------------------------------ the ceiling


def test_shared_tradecraft_alone_caps_at_low() -> None:
    evidence = [_item("E1", "vendor", EvidenceType.TACTICS, a=Consistency.CONSISTENT, b=Consistency.INCONSISTENT)]
    assert ceiling(evidence) == "low"
    assert "cannot support more than low" in " ".join(derived_grade(evidence)["reasons"])


def test_one_diagnostic_item_from_one_source_caps_at_moderate() -> None:
    evidence = [
        _item("E1", "vendor A", EvidenceType.INFRASTRUCTURE, a=Consistency.CONSISTENT, b=Consistency.INCONSISTENT)
    ]
    assert ceiling(evidence) == "moderate"


def test_two_independent_sources_of_diagnostic_evidence_allow_high() -> None:
    evidence = [
        _item("E1", "vendor A", EvidenceType.INFRASTRUCTURE, a=Consistency.CONSISTENT, b=Consistency.INCONSISTENT),
        _item("E2", "vendor B", EvidenceType.CODE, a=Consistency.CONSISTENT, b=Consistency.INCONSISTENT),
    ]
    assert ceiling(evidence) == "high"
    assert derived_grade(evidence)["profile"]["independent_sources"] == 2


def test_a_diagnostic_item_that_does_not_discriminate_does_not_raise_the_ceiling() -> None:
    """Infrastructure every hypothesis explains is not evidence of sameness."""
    evidence = [
        _item("E1", "vendor A", EvidenceType.INFRASTRUCTURE, a=Consistency.CONSISTENT, b=Consistency.CONSISTENT)
    ]
    assert ceiling(evidence) == "low"


def test_the_same_source_twice_is_not_independence() -> None:
    evidence = [
        _item("E1", "Vendor A", EvidenceType.INFRASTRUCTURE, a=Consistency.CONSISTENT, b=Consistency.INCONSISTENT),
        _item("E2", " vendor a ", EvidenceType.CODE, a=Consistency.CONSISTENT, b=Consistency.INCONSISTENT),
    ]
    assert ceiling(evidence) == "moderate"


def test_a_grade_above_the_ceiling_is_a_high_finding() -> None:
    evidence = [_item("E1", "vendor", EvidenceType.TACTICS, a=Consistency.CONSISTENT)]
    findings = check_declared("high", evidence)
    assert findings[0]["code"] == "grade-exceeds-evidence"
    assert findings[0]["severity"] == "high"


def test_a_more_cautious_grade_is_allowed() -> None:
    evidence = [
        _item("E1", "A", EvidenceType.CODE, a=Consistency.CONSISTENT, b=Consistency.INCONSISTENT),
        _item("E2", "B", EvidenceType.CODE, a=Consistency.CONSISTENT, b=Consistency.INCONSISTENT),
    ]
    assert check_declared("low", evidence) == []


def test_no_grade_is_refused_not_defaulted() -> None:
    assert check_declared(None, [])[0]["code"] == "no-grade"


# ------------------------------------------------------------------ the contract


def test_exit_codes_are_the_contract() -> None:
    assert exit_code([]) == 0
    assert exit_code([finding("x", "medium", "m")]) == 0
    assert exit_code([finding("x", "high", "h")]) == 1


def test_severity_counts_cover_all_three() -> None:
    counts = severity_counts([finding("a", "high", ""), finding("b", "low", "")])
    assert counts == {"high": 1, "medium": 0, "low": 1}


def test_an_unreadable_file_raises_cannot_check(tmp_path) -> None:
    with pytest.raises(CannotCheck):
        read_json(tmp_path / "missing.json")


def test_invalid_json_raises_cannot_check(tmp_path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{", encoding="utf-8")
    with pytest.raises(CannotCheck):
        read_json(path)


# ------------------------------------------------------------------ one validator


def _bundle(marking: dict | None = None) -> dict:
    marking = marking or marking_object("amber")
    return {
        "type": "bundle",
        "id": "bundle--11111111-1111-4111-8111-111111111111",
        "objects": [
            marking,
            {
                "type": "indicator",
                "spec_version": "2.1",
                "id": "indicator--22222222-2222-4222-8222-222222222222",
                "created": "2026-10-01T00:00:00Z",
                "modified": "2026-10-01T00:00:00Z",
                "pattern": "[domain-name:value = 'x.test']",
                "pattern_type": "stix",
                "valid_from": "2026-10-01T00:00:00Z",
                "object_marking_refs": [marking["id"]],
            },
        ],
    }


def test_a_well_formed_bundle_is_valid_and_has_one_marking() -> None:
    assert validate_bundle(_bundle())["valid"] is True
    assert effective_marking(_bundle()) == "AMBER"


def test_spec_version_missing_is_high() -> None:
    bundle = _bundle()
    bundle["objects"][1].pop("spec_version")
    assert "stix-spec-version-missing" in {item["code"] for item in validate_bundle(bundle)["findings"]}


def test_an_expired_indicator_is_reported_only_when_a_date_is_given() -> None:
    bundle = _bundle()
    bundle["objects"][1]["valid_until"] = "2026-01-01T00:00:00Z"
    assert "stix-expired-indicator" not in {item["code"] for item in validate_bundle(bundle)["findings"]}
    dated = validate_bundle(bundle, today="2026-06-01")
    assert "stix-expired-indicator" in {item["code"] for item in dated["findings"]}


def test_marking_definitions_are_the_official_tlp_2_0_objects() -> None:
    marking = marking_object("clear")
    assert marking["id"] == TLP["CLEAR"]["id"]
    assert marking["name"] == "TLP:CLEAR"
    assert marking["created"] == "2022-10-01T00:00:00.000Z"
    assert marking["extensions"]["extension-definition--60a3c5c5-0d10-413e-aab3-9e08dde9e88d"]["tlp_2_0"] == "clear"


def test_white_is_refused_by_the_factory() -> None:
    with pytest.raises(ValueError, match="deprecated"):
        marking_object("white")


# ------------------------------------------------------------------ traceability


def test_a_mismatched_trace_id_is_high() -> None:
    result = link({"assessment_id": "a-1"}, "assessment_id", {"id": "a-2"}, label="assessment")
    assert result["findings"][0]["code"] == "trace-mismatch"


def test_a_missing_link_is_adopted_from_the_file() -> None:
    result = link({}, "assessment_id", {"id": "a-2"}, label="assessment")
    assert result["id"] == "a-2"
    assert result["findings"] == []


def test_an_unknown_requirement_is_high() -> None:
    register = {"id": "R", "requirements": [{"id": "PIR-001"}]}
    result = link_requirement({"requirement_id": "PIR-999"}, register)
    assert result["findings"][0]["code"] == "trace-unknown-requirement"


def test_external_references_keep_the_cycle_order() -> None:
    references = external_references({"pir": "PIR-001", "assessment": "a-1", "hunt": None})
    assert references == [
        {"source_name": "cti-suite:pir", "external_id": "PIR-001"},
        {"source_name": "cti-suite:assessment", "external_id": "a-1"},
    ]


def test_id_of_falls_back_to_the_specific_identifiers() -> None:
    assert id_of({"assessment_id": "a-1"}) == "a-1"
    assert id_of({"requirements": []}) is None
