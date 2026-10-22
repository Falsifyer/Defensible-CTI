"""One STIX validator, not two.

The factory and the gate used to have separate implementations with separate severity
tables, so the same bundle could be valid for one and invalid for the other. These tests
pin the single implementation: for any bundle, both report the same findings.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from cti_method.stix import TLP, validate_bundle
from sharegate.core import check_stix, pre_share
from stixforge.build import build
from stixforge.validate import validate

ROOT = Path(__file__).resolve().parents[3]
PRODUCT = json.loads((ROOT / "packages" / "stixforge" / "examples" / "product.json").read_text(encoding="utf-8"))
PRODUCT["created"] = "2026-10-22T00:00:00Z"


def _mutations(bundle: dict) -> dict[str, dict]:
    variants: dict[str, dict] = {}
    variants["valid"] = copy.deepcopy(bundle)

    unmarked = copy.deepcopy(bundle)
    next(o for o in unmarked["objects"] if o["type"] == "indicator").pop("object_marking_refs")
    variants["unmarked"] = unmarked

    dangling = copy.deepcopy(bundle)
    report = next(o for o in dangling["objects"] if o["type"] == "report")
    report["object_refs"].append("indicator--00000000-0000-4000-8000-000000000000")
    variants["dangling"] = dangling

    duplicate = copy.deepcopy(bundle)
    duplicate["objects"].append(copy.deepcopy(duplicate["objects"][-1]))
    variants["duplicate"] = duplicate

    bad_version = copy.deepcopy(bundle)
    bad_version["objects"][1]["spec_version"] = "2.0"
    variants["bad-version"] = bad_version

    no_pattern = copy.deepcopy(bundle)
    next(o for o in no_pattern["objects"] if o["type"] == "indicator").pop("pattern")
    variants["no-pattern"] = no_pattern

    return variants


@pytest.mark.parametrize("name", ["valid", "unmarked", "dangling", "duplicate", "bad-version", "no-pattern"])
def test_the_factory_and_the_gate_report_the_same_findings(name: str) -> None:
    bundle = _mutations(build(PRODUCT))[name]
    factory = validate(bundle)["findings"]
    gate = check_stix(bundle)["findings"]
    assert factory == gate


def test_the_validator_itself_is_the_shared_one() -> None:
    bundle = build(PRODUCT)
    assert validate(bundle) == validate_bundle(bundle)


def test_a_clear_bundle_of_iocs_passes_the_gate() -> None:
    """The reported regression: TLP:CLEAR plus an IP observable used to be refused."""
    bundle = build({**PRODUCT, "tlp": "clear"})
    result = pre_share(bundle)
    assert result["shareable"] is True, result["findings"]
    assert result["effective_tlp"] == "TLP:CLEAR"
    assert "tlp-deprecated" not in {item["code"] for item in result["findings"]}


def test_the_factory_never_emits_deprecated_white() -> None:
    with pytest.raises(ValueError, match="deprecated"):
        build({**PRODUCT, "tlp": "white"})


def test_tlp_2_0_markings_are_the_official_ones() -> None:
    assert TLP["CLEAR"]["id"] == "marking-definition--94868c89-83c2-464b-929b-a1a8aa3c8487"
    assert TLP["AMBER+STRICT"]["id"] == "marking-definition--939a9414-2ddd-4d32-a0cd-375ea402b003"
    assert {entry["name"] for entry in TLP.values()} == {
        "TLP:CLEAR",
        "TLP:GREEN",
        "TLP:AMBER",
        "TLP:AMBER+STRICT",
        "TLP:RED",
    }
