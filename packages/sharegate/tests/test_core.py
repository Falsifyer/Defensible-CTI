"""Objective tests: the ground truth is the TLP 2.0 rules and the STIX 2.1 shape."""

from __future__ import annotations

from cti_method.stix import TLP

from sharegate.core import check_stix, check_tlp, pre_share, tlp_policy

MARKING = {
    "type": "marking-definition",
    "spec_version": "2.1",
    "id": TLP["CLEAR"]["id"],
    "created": "2022-10-01T00:00:00.000Z",
    "name": "TLP:CLEAR",
    "extensions": {
        "extension-definition--60a3c5c5-0d10-413e-aab3-9e08dde9e88d": {
            "extension_type": "property-extension",
            "tlp_2_0": "clear",
        }
    },
}

VALID_BUNDLE = {
    "type": "bundle",
    "id": "bundle--11111111-1111-4111-8111-111111111111",
    "objects": [
        MARKING,
        {
            "type": "indicator",
            "spec_version": "2.1",
            "id": "indicator--22222222-2222-4222-8222-222222222222",
            "created": "2026-10-09T00:00:00Z",
            "modified": "2026-10-09T00:00:00Z",
            "pattern": "[ipv4-addr:value = '192.0.2.1']",
            "pattern_type": "stix",
            "valid_from": "2026-10-09T00:00:00Z",
            "object_marking_refs": [MARKING["id"]],
        },
    ],
}


def _codes(result: dict) -> list[str]:
    return [item["code"] for item in result["findings"]]


def test_policy_table_matches_tlp_2_0() -> None:
    table = {row["marking"]: row for row in tlp_policy()}
    assert table["TLP:RED"]["rank"] == 5
    assert table["TLP:AMBER+STRICT"]["rank"] == 4
    assert table["TLP:WHITE"]["deprecated"] is True
    assert "TLP:CLEAR" in table


def test_a_correct_marking_is_clean() -> None:
    result = check_tlp("TLP:AMBER\nvictim infrastructure")
    assert result["effective"] == "TLP:AMBER"
    assert result["findings"] == []


def test_a_missing_marking_is_flagged() -> None:
    result = check_tlp("no handling caveat here")
    assert _codes(result) == ["tlp-missing"]


def test_deprecated_white_is_flagged() -> None:
    result = check_tlp("TLP:WHITE")
    assert "tlp-deprecated" in _codes(result)


def test_conflicting_markings_are_high_severity() -> None:
    result = check_tlp("TLP:RED and TLP:CLEAR")
    finding = next(item for item in result["findings"] if item["code"] == "tlp-conflict")
    assert finding["severity"] == "high"
    assert result["effective"] is None


def test_permissive_marking_on_sensitive_text_is_flagged_but_does_not_block() -> None:
    """The heuristic is a guard, not a classifier: it cannot refuse a product."""
    result = check_tlp("TLP:CLEAR\nvictim@example.com and 192.168.1.5")
    finding = next(item for item in result["findings"] if item["code"] == "tlp-sensitive-permissive")
    assert finding["severity"] == "medium"
    assert pre_share("TLP:CLEAR\nvictim@example.com and 192.168.1.5")["shareable"] is True


def test_a_clear_bundle_of_iocs_is_not_blocked() -> None:
    """Regression: an IP inside a cyber-observable is an indicator, not a leak.

    The old gate ran the sensitive-content regex over the serialised bundle, so every
    TLP:CLEAR bundle of IOCs — the normal case in CTI — was refused.
    """
    bundle = {
        **VALID_BUNDLE,
        "objects": [
            MARKING,
            {
                "type": "ipv4-addr",
                "spec_version": "2.1",
                "id": "ipv4-addr--33333333-3333-4333-8333-333333333333",
                "value": "198.51.100.7",
            },
            VALID_BUNDLE["objects"][1],
        ],
    }
    result = pre_share(bundle)
    assert result["shareable"] is True, result["findings"]
    assert result["effective_tlp"] == "TLP:CLEAR"


def test_marking_is_resolved_by_reference_not_by_text() -> None:
    """A marking definition that nothing references does not travel with the content."""
    unused = {**MARKING, "id": TLP["GREEN"]["id"], "name": "TLP:GREEN"}
    bundle = {**VALID_BUNDLE, "objects": [MARKING, unused, *VALID_BUNDLE["objects"]]}
    result = check_tlp(bundle)
    assert result["effective"] == "TLP:CLEAR"
    assert "tlp-conflict" not in _codes(result)


def test_two_referenced_markings_that_disagree_are_a_conflict() -> None:
    green = {**MARKING, "id": TLP["GREEN"]["id"], "name": "TLP:GREEN"}
    malware = {
        "type": "malware",
        "spec_version": "2.1",
        "id": "malware--77777777-7777-4777-8777-777777777777",
        "created": "2026-10-09T00:00:00Z",
        "modified": "2026-10-09T00:00:00Z",
        "name": "x",
        "is_family": False,
        "malware_types": ["unknown"],
        "object_marking_refs": [green["id"]],
    }
    bundle = {**VALID_BUNDLE, "objects": [MARKING, green, VALID_BUNDLE["objects"][1], malware]}
    result = check_tlp(bundle)
    assert "tlp-conflict" in _codes(result)
    assert not result["clean"]


def test_who_is_who_on_the_object_marking_refs() -> None:
    bundle = {**VALID_BUNDLE, "objects": [MARKING, {**VALID_BUNDLE["objects"][1], "object_marking_refs": []}]}
    result = pre_share(bundle)
    assert result["shareable"] is False
    assert "stix-no-marking" in _codes(result)


def test_a_valid_bundle_passes() -> None:
    result = check_stix(VALID_BUNDLE)
    assert result["valid"] is True, result["findings"]
    assert result["findings"] == []


def test_non_bundle_and_non_object_are_high() -> None:
    assert check_stix({"type": "report"})["valid"] is False
    assert check_stix("not a dict")["findings"][0]["code"] == "stix-not-object"


def test_id_type_mismatch_and_duplicates_are_high() -> None:
    bundle = {
        "type": "bundle",
        "id": "bundle--11111111-1111-4111-8111-111111111111",
        "objects": [
            {"type": "indicator", "id": "malware--44444444-4444-4444-8444-444444444444", "spec_version": "2.1"},
            {"type": "indicator", "id": "indicator--55555555-5555-4555-8555-555555555555", "spec_version": "2.1"},
            {"type": "indicator", "id": "indicator--55555555-5555-4555-8555-555555555555", "spec_version": "2.1"},
        ],
    }
    codes = _codes(check_stix(bundle))
    assert "stix-id-type-mismatch" in codes
    assert "stix-duplicate-id" in codes


def test_spec_version_is_checked() -> None:
    wrong = {
        "type": "bundle",
        "id": "bundle--11111111-1111-4111-8111-111111111111",
        "objects": [
            {"type": "indicator", "id": "indicator--66666666-6666-4666-8666-666666666666", "spec_version": "2.0"}
        ],
    }
    missing = {
        "type": "bundle",
        "id": "bundle--11111111-1111-4111-8111-111111111111",
        "objects": [{"type": "indicator", "id": "indicator--66666666-6666-4666-8666-666666666666"}],
    }
    assert "stix-spec-version" in _codes(check_stix(wrong))
    assert "stix-spec-version-missing" in _codes(check_stix(missing))


def test_pre_share_blocks_on_high_and_passes_otherwise() -> None:
    assert pre_share("TLP:RED\nfor your eyes only")["shareable"] is True
    blocked = pre_share("TLP:CLEAR and TLP:RED")
    assert blocked["shareable"] is False
    assert blocked["by_severity"]["high"] >= 1


def test_pre_share_runs_the_stix_gate_on_a_bundle() -> None:
    result = pre_share({**VALID_BUNDLE, "objects": [{"type": "indicator", "id": "wrong--a"}]})
    assert result["stix"] is not None
    assert result["shareable"] is False


def test_expired_indicators_are_reported_when_a_date_is_given() -> None:
    bundle = {
        **VALID_BUNDLE,
        "objects": [
            MARKING,
            {**VALID_BUNDLE["objects"][1], "valid_until": "2026-01-01T00:00:00Z"},
        ],
    }
    assert "stix-expired-indicator" not in _codes(pre_share(bundle)["stix"])
    assert "stix-expired-indicator" in _codes(pre_share(bundle, today="2026-06-01")["stix"])


def test_a_bundle_whose_indicators_all_expired_is_not_shareable() -> None:
    bundle = {
        **VALID_BUNDLE,
        "objects": [
            MARKING,
            {**VALID_BUNDLE["objects"][1], "valid_until": "2026-01-01T00:00:00Z"},
        ],
    }
    result = pre_share(bundle, today="2026-06-01")
    assert result["shareable"] is False
    assert "stix-all-indicators-expired" in _codes(result)


def test_the_gate_reports_that_it_could_not_check() -> None:
    from unittest import mock

    unavailable = {"valid": False, "checked": False, "findings": [], "by_severity": {}, "objects": 0}
    with mock.patch("sharegate.core.validate_bundle", return_value=unavailable):
        assert pre_share(VALID_BUNDLE)["checked"] is False
