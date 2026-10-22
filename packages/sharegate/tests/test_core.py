"""Objective tests: the ground truth is the TLP 2.0 rules and the STIX 2.1 shape."""

from __future__ import annotations

from sharegate.core import check_stix, check_tlp, pre_share, tlp_policy

VALID_BUNDLE = {
    "type": "bundle",
    "id": "bundle--11111111-1111-4111-8111-111111111111",
    "objects": [
        {
            "type": "indicator",
            "spec_version": "2.1",
            "id": "indicator--22222222-2222-4222-8222-222222222222",
            "created": "2026-10-09T00:00:00Z",
            "modified": "2026-10-09T00:00:00Z",
        }
    ],
}


def test_policy_table_matches_tlp_2_0() -> None:
    table = {row["marking"]: row for row in tlp_policy()}
    assert table["TLP:RED"]["rank"] == 5
    assert table["TLP:WHITE"]["deprecated"] is True
    assert "TLP:CLEAR" in table


def test_a_correct_marking_is_clean() -> None:
    result = check_tlp("TLP:AMBER\nvictim infrastructure")
    assert result["effective"] == "TLP:AMBER"
    assert result["findings"] == []


def test_a_missing_marking_is_flagged() -> None:
    result = check_tlp("no handling caveat here")
    assert [f["code"] for f in result["findings"]] == ["tlp-missing"]


def test_deprecated_white_is_flagged() -> None:
    result = check_tlp("TLP:WHITE")
    assert "tlp-deprecated" in [f["code"] for f in result["findings"]]


def test_conflicting_markings_are_high_severity() -> None:
    result = check_tlp("TLP:RED and TLP:CLEAR")
    finding = next(f for f in result["findings"] if f["code"] == "tlp-conflict")
    assert finding["severity"] == "high"
    assert result["effective"] is None


def test_permissive_marking_on_sensitive_content_is_blocked() -> None:
    result = check_tlp("TLP:CLEAR\nvictim@example.com and 192.168.1.5")
    finding = next(f for f in result["findings"] if f["code"] == "tlp-sensitive-permissive")
    assert finding["severity"] == "high"


def test_a_valid_bundle_passes() -> None:
    result = check_stix(VALID_BUNDLE)
    assert result["valid"] is True
    assert result["findings"] == []


def test_non_bundle_and_non_object_are_high() -> None:
    assert check_stix({"type": "report"})["valid"] is False
    assert check_stix("not a dict")["findings"][0]["code"] == "stix-not-object"


def test_id_type_mismatch_and_duplicates_are_high() -> None:
    bundle = {
        "type": "bundle",
        "id": "bundle--x",
        "objects": [
            {"type": "indicator", "id": "malware--a", "spec_version": "2.1"},
            {"type": "indicator", "id": "indicator--b", "spec_version": "2.1"},
            {"type": "indicator", "id": "indicator--b", "spec_version": "2.1"},
        ],
    }
    codes = [f["code"] for f in check_stix(bundle)["findings"]]
    assert "stix-id-type-mismatch" in codes
    assert "stix-duplicate-id" in codes


def test_spec_version_is_checked() -> None:
    wrong = {
        "type": "bundle",
        "id": "bundle--x",
        "objects": [{"type": "indicator", "id": "indicator--a", "spec_version": "2.0"}],
    }
    missing = {"type": "bundle", "id": "bundle--x", "objects": [{"type": "indicator", "id": "indicator--a"}]}
    assert "stix-spec-version" in [f["code"] for f in check_stix(wrong)["findings"]]
    assert "stix-spec-version-missing" in [f["code"] for f in check_stix(missing)["findings"]]


def test_pre_share_blocks_on_high_and_passes_otherwise() -> None:
    assert pre_share("TLP:RED\nfor your eyes only")["shareable"] is True
    blocked = pre_share("TLP:CLEAR\nvictim 10.0.0.1")
    assert blocked["shareable"] is False
    assert blocked["by_severity"]["high"] >= 1


def test_pre_share_runs_the_stix_gate_on_a_bundle() -> None:
    result = pre_share({**VALID_BUNDLE, "objects": [{"type": "indicator", "id": "wrong--a"}]})
    assert result["stix"] is not None
    assert result["shareable"] is False
