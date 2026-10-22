"""Tests for the ingest adapters."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cryptonym.ingest import load
from cryptonym.ingest.attack_stix import designations_from_attack_bundle
from cryptonym.ingest.misp_galaxy import designations_from_galaxies, designations_from_galaxy
from cryptonym.ingest.opencti import designations_from_opencti_actor


def test_galaxy_keeps_synonyms_apart() -> None:
    designations = designations_from_galaxy(
        {"value": "APT28", "meta": {"synonyms": ["Fancy Bear", "Sofacy"], "refs": ["https://x"]}}
    )
    assert [d.name for d in designations] == ["APT28", "Fancy Bear", "Sofacy"]
    assert all(d.vendor == "misp-galaxy" for d in designations)


def test_galaxy_without_value_fails_closed() -> None:
    with pytest.raises(ValueError, match="value"):
        designations_from_galaxy({"meta": {}})


def test_many_galaxies_deduplicate() -> None:
    clusters = [{"value": "APT28"}, {"value": "APT28", "meta": {"synonyms": ["Sofacy"]}}]
    names = sorted(d.name for d in designations_from_galaxies(clusters))
    assert names == ["APT28", "Sofacy"]


def test_attack_bundle_maps_intrusion_sets_only() -> None:
    bundle = {
        "objects": [
            {"type": "intrusion-set", "name": "Volt Typhoon", "aliases": ["Vanguard Panda"]},
            {"type": "malware", "name": "Not Me"},
        ]
    }
    designations = designations_from_attack_bundle(bundle)
    assert {d.name for d in designations} == {"Volt Typhoon", "Vanguard Panda"}
    assert all(d.vendor == "mitre-attack" for d in designations)


def test_opencti_actor_uses_created_by_as_vendor() -> None:
    designations = designations_from_opencti_actor(
        {"name": "Scattered Spider", "aliases": ["UNC3944"], "createdBy": "OpenCTI"}
    )
    assert {d.name for d in designations} == {"Scattered Spider", "UNC3944"}
    assert all(d.vendor == "OpenCTI" for d in designations)


def test_opencti_actor_without_name_fails_closed() -> None:
    with pytest.raises(ValueError, match="name"):
        designations_from_opencti_actor({"aliases": ["x"]})


def test_load_dispatches_each_source(tmp_path: Path) -> None:
    galaxy = tmp_path / "galaxy.json"
    galaxy.write_text(json.dumps({"values": [{"value": "APT28"}]}), encoding="utf-8")
    assert [d.name for d in load("misp-galaxy", galaxy)] == ["APT28"]

    attack = tmp_path / "attack.json"
    attack.write_text(json.dumps({"objects": [{"type": "intrusion-set", "name": "APT29"}]}), encoding="utf-8")
    assert [d.name for d in load("attack-stix", attack)] == ["APT29"]

    opencti = tmp_path / "opencti.json"
    opencti.write_text(json.dumps({"name": "APT31"}), encoding="utf-8")
    assert [d.name for d in load("opencti", opencti)] == ["APT31"]


def test_load_rejects_unknown_source(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unsupported source"):
        load("nope", tmp_path / "x.json")
