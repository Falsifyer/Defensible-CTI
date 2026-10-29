"""The shared core: the ceiling, one validator, one contract, one trace."""

from __future__ import annotations

import pytest

from cti_method.ach import inconsistency_scores, least_inconsistent
from cti_method.contract import CannotCheck, exit_code, finding, read_json, severity_counts
from cti_method.evidence import Consistency, Evidence, EvidenceType
from cti_method.grading import ceiling, check_declared, derived_grade, profile
from cti_method.stix import TLP, effective_marking, marking_object, validate_bundle
from cti_method.trace import content_hash, external_references, id_of, link, link_requirement


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


def test_shared_tradecraft_cannot_undo_the_contradiction_downgrade() -> None:
    """A4: an item consistent with every hypothesis is not support for the favoured one.

    Without this guard a shared-tradecraft item raises the ceiling by blocking the
    contradiction step instead of leaving the grade where the evidence put it.
    """
    sources = [{"id": "a", "publisher": "A"}, {"id": "b", "publisher": "B"}, {"id": "c", "publisher": "C"}]
    base = [
        Evidence(id="E1", statement="s", source="A", type=EvidenceType.INFRASTRUCTURE,
                 consistency={"H1": Consistency.INCONSISTENT, "H2": Consistency.INCONSISTENT},
                 source_id="a", reliability="A"),
        Evidence(id="E2", statement="s", source="B", type=EvidenceType.INFRASTRUCTURE,
                 consistency={"H1": Consistency.INCONSISTENT, "H2": Consistency.CONSISTENT},
                 source_id="b", reliability="D"),
    ]
    shared = Evidence(id="E3", statement="s", source="C", type=EvidenceType.INFRASTRUCTURE,
                      consistency={"H1": Consistency.CONSISTENT, "H2": Consistency.CONSISTENT},
                      source_id="c", reliability="C")
    assert derived_grade(base, sources, "H2")["ceiling"] == "moderate"
    assert derived_grade([*base, shared], sources, "H2")["ceiling"] == "moderate"


def test_a_document_too_deep_for_the_parser_is_cannot_check(tmp_path) -> None:
    path = tmp_path / "deep.json"
    path.write_text("[" * 100_000 + "]" * 100_000, encoding="utf-8")
    with pytest.raises(CannotCheck):
        read_json(path)


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
    result = link({"assessment_id": "a-1"}, "assessment_id", {"id": "a-2"}, label="assessment", kind="assessment")
    assert result["findings"][0]["code"] == "trace-mismatch"


def test_a_missing_link_is_adopted_from_the_file() -> None:
    result = link({}, "assessment_id", {"id": "a-2"}, label="assessment", kind="assessment")
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


def test_id_of_is_explicit_per_artifact_kind() -> None:
    assert id_of({"assessment_id": "a-1", "id": "wrong"}, "assessment") == "a-1"
    assert id_of({"hunt_id": "HUNT-1", "id": "wrong"}, "hunt") == "HUNT-1"
    assert id_of({"id": "only"}, "product") == "only"
    with pytest.raises(TypeError):
        id_of({"id": "no-kind"})


# ------------------------------------------------------------------ sources and independence


def test_two_sources_that_derive_from_one_are_one_voice() -> None:
    sources = [
        {"id": "a", "publisher": "Vendor A"},
        {"id": "b", "publisher": "Blog B", "derived_from": ["a"]},
    ]
    evidence = [
        Evidence(
            "E1", "s", "Vendor A", EvidenceType.CODE,
            {"x": Consistency.CONSISTENT, "y": Consistency.INCONSISTENT}, "a",
        ),
        Evidence(
            "E2", "s", "Blog B", EvidenceType.INFRASTRUCTURE,
            {"x": Consistency.CONSISTENT, "y": Consistency.INCONSISTENT}, "b",
        ),
    ]
    described = profile(evidence, sources)
    assert described.independent_sources == 1
    assert ceiling(evidence, sources) == "moderate"


def test_two_reports_from_one_publisher_are_one_voice_even_with_different_ids() -> None:
    sources = [
        {"id": "a1", "publisher": "Vendor A"},
        {"id": "a2", "publisher": "vendor a"},
    ]
    evidence = [
        Evidence(
            "E1", "s", "x", EvidenceType.CODE,
            {"x": Consistency.CONSISTENT, "y": Consistency.INCONSISTENT}, "a1",
        ),
        Evidence(
            "E2", "s", "y", EvidenceType.CODE,
            {"x": Consistency.CONSISTENT, "y": Consistency.INCONSISTENT}, "a2",
        ),
    ]
    assert profile(evidence, sources).independent_sources == 1


def test_two_independent_registered_sources_allow_high() -> None:
    sources = [{"id": "a", "publisher": "Vendor A"}, {"id": "b", "publisher": "Vendor B"}]
    evidence = [
        Evidence(
            "E1", "s", "x", EvidenceType.CODE,
            {"x": Consistency.CONSISTENT, "y": Consistency.INCONSISTENT}, "a",
        ),
        Evidence(
            "E2", "s", "y", EvidenceType.INFRASTRUCTURE,
            {"x": Consistency.CONSISTENT, "y": Consistency.INCONSISTENT}, "b",
        ),
    ]
    assert ceiling(evidence, sources) == "high"
    assert profile(evidence, sources).registered is True


def test_contradiction_lowers_the_ceiling_a_step() -> None:
    sources = [{"id": "a", "publisher": "A"}, {"id": "b", "publisher": "B"}]
    supporting = [
        Evidence("E1", "s", "x", EvidenceType.CODE, {"x": Consistency.CONSISTENT}, "a"),
        Evidence("E2", "s", "y", EvidenceType.INFRASTRUCTURE, {"x": Consistency.CONSISTENT}, "b"),
    ]
    contradicting = [
        Evidence("E3", "s", "x", EvidenceType.INFRASTRUCTURE, {"x": Consistency.INCONSISTENT}, "a"),
        Evidence("E4", "s", "y", EvidenceType.CODE, {"x": Consistency.INCONSISTENT}, "b"),
        Evidence("E5", "s", "z", EvidenceType.OPERATOR, {"x": Consistency.INCONSISTENT}, "a"),
    ]
    evidence = supporting + contradicting
    assert ceiling(evidence, sources) == "high"
    assert ceiling(evidence, sources, "x") == "moderate"


# ------------------------------------------------------------------ pesos


def test_reliability_weights_the_contradiction_score() -> None:
    evidence = [
        Evidence("E1", "s", "x", EvidenceType.CODE, {"h": Consistency.INCONSISTENT}, reliability="A"),
        Evidence("E2", "s", "y", EvidenceType.CODE, {"h": Consistency.INCONSISTENT}, reliability="E"),
        Evidence("E3", "s", "z", EvidenceType.CODE, {"g": Consistency.INCONSISTENT}, reliability="D"),
    ]
    scores = inconsistency_scores(evidence, ["h", "g"])
    assert scores["h"] == 1.2
    assert scores["g"] == 0.4
    assert least_inconsistent(evidence, ["h", "g"]) == ["g", "h"]


def test_without_a_reliability_band_every_item_weighs_the_same() -> None:
    evidence = [
        Evidence("E1", "s", "x", EvidenceType.CODE, {"h": Consistency.INCONSISTENT}),
        Evidence("E2", "s", "y", EvidenceType.CODE, {"g": Consistency.INCONSISTENT}),
    ]
    assert inconsistency_scores(evidence, ["h", "g"]) == {"h": 1.0, "g": 1.0}


# ------------------------------------------------------------------ probabilidad y limites


def test_brier_score_scores_the_estimative_axis() -> None:
    from cti_method.metrics import probability_calibration

    result = probability_calibration([("likely", True), ("likely", True), ("unlikely", False)])
    assert result["n"] == 3
    assert result["brier_score"] == 0.1225
    assert result["buckets"]["likely"]["observed_rate"] == 1.0
    assert result["buckets"]["unlikely"]["observed_rate"] == 0.0


def test_a_fifty_fifty_forecast_scores_a_quarter() -> None:
    from cti_method.metrics import probability_calibration

    result = probability_calibration([("roughly_even_chance", True), ("roughly_even_chance", False)])
    assert result["brier_score"] == 0.25


def test_records_without_a_probability_are_not_scored() -> None:
    from cti_method.metrics import probability_calibration

    assert probability_calibration([(None, True)])["n"] == 0


def test_reading_over_the_size_limit_fails_closed(tmp_path) -> None:
    path = tmp_path / "big.json"
    path.write_text('{"a": 1}', encoding="utf-8")
    with pytest.raises(CannotCheck, match="over the"):
        read_json(path, limit=4)


def test_deep_nesting_is_refused(tmp_path) -> None:
    path = tmp_path / "deep.json"
    path.write_text("[" * 70 + "]" * 70, encoding="utf-8")
    with pytest.raises(CannotCheck, match="deeper"):
        read_json(path, max_depth=10)


def test_a_bundle_over_the_object_limit_is_not_checked() -> None:
    bundle = _bundle()
    result = validate_bundle(bundle, max_objects=1)
    assert result["checked"] is False
    assert "stix-too-large" in {item["code"] for item in result["findings"]}


def test_every_indicator_expired_is_a_high_finding() -> None:
    bundle = _bundle()
    bundle["objects"][1]["valid_until"] = "2026-01-01T00:00:00Z"
    result = validate_bundle(bundle, today="2026-06-01")
    assert "stix-all-indicators-expired" in {item["code"] for item in result["findings"]}
    assert result["valid"] is False


def test_a_changed_upstream_is_detected_by_its_hash() -> None:
    upstream = {"id": "a-1", "x": 1}
    digest = content_hash(upstream)
    result = link(
        {"assessment_id": "a-1", "assessment_hash": "0" * 64},
        "assessment_id",
        upstream,
        label="assessment",
        kind="assessment",
    )
    assert result["findings"][0]["code"] == "trace-hash-mismatch"
    assert result["hash"] == digest
    assert link(
        {"assessment_id": "a-1", "assessment_hash": digest},
        "assessment_id",
        upstream,
        label="assessment",
        kind="assessment",
    )["findings"] == []


def test_external_references_pin_the_hash() -> None:
    references = external_references({"assessment": "a-1"}, {"assessment": "0123456789abcdef"})
    assert references == [{"source_name": "cti-suite:assessment", "external_id": "a-1@0123456789ab"}]
