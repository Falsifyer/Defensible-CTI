import json
from pathlib import Path

import pytest

from stixforge.build import build
from stixforge.markings import TLP, marking_object

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
PRODUCTO = json.loads((EXAMPLES / "product.json").read_text(encoding="utf-8"))


def test_the_bundle_has_marking_identity_and_report():
    b = build(PRODUCTO)
    tipos = [o["type"] for o in b["objects"]]
    assert b["type"] == "bundle"
    assert "marking-definition" in tipos
    assert "identity" in tipos
    assert "report" in tipos


def test_it_is_byte_for_byte_deterministic():
    assert json.dumps(build(PRODUCTO)) == json.dumps(build(PRODUCTO))


def test_the_report_references_everything_shareable():
    b = build(PRODUCTO)
    report = next(o for o in b["objects"] if o["type"] == "report")
    ids = {o["id"] for o in b["objects"]}
    assert report["object_refs"]
    assert set(report["object_refs"]) <= ids
    assert len(report["object_refs"]) == 5  # 2 observables + 2 indicadores + 1 malware


def test_every_sdo_is_marked_and_scos_do_not_need_it():
    b = build(PRODUCTO)
    sco = {"domain-name", "ipv4-addr", "ipv6-addr", "url", "file", "email-addr"}
    for o in b["objects"]:
        if o["type"] == "marking-definition" or o["type"] in sco:
            continue
        assert o["object_marking_refs"], o["id"]
    for o in b["objects"]:
        if o["type"] in sco:
            # In 2.1 an SCO carries no created, modified, created_by_ref or marking.
            assert set(o) <= {"type", "spec_version", "id", "value", "hashes"}


def test_clear_uses_the_official_tlp_2_0_marking():
    b = build({**PRODUCTO, "tlp": "clear"})
    marking = next(o for o in b["objects"] if o["type"] == "marking-definition")
    assert marking["id"] == TLP["CLEAR"]["id"]
    assert marking["name"] == "TLP:CLEAR"
    assert marking["extensions"]


def test_amber_strict_is_a_first_class_marking():
    marking = marking_object("amber+strict")
    assert marking["id"] == TLP["AMBER+STRICT"]["id"]
    assert marking["name"] == "TLP:AMBER+STRICT"


def test_white_is_deprecated_and_not_emitted():
    with pytest.raises(ValueError, match="deprecated"):
        marking_object("TLP:WHITE")


def test_the_example_ships_as_amber():
    b = build(PRODUCTO)
    marking = next(o for o in b["objects"] if o["type"] == "marking-definition")
    assert marking["id"] == TLP["AMBER"]["id"]


def test_without_created_it_fails_instead_of_forging_a_new_version_with_the_same_id():
    sin_fecha = {k: v for k, v in PRODUCTO.items() if k != "created"}
    with pytest.raises(ValueError, match="created"):
        build(sin_fecha)


def test_without_a_title_it_fails():
    with pytest.raises(ValueError, match="title"):
        build({**PRODUCTO, "title": ""})


def test_without_an_author_it_fails():
    with pytest.raises(ValueError, match="author"):
        build({**PRODUCTO, "author": ""})


def test_without_a_tlp_it_fails_instead_of_defaulting_to_clear():
    """C1: a forgotten marking is not a public product."""
    sin_tlp = {k: v for k, v in PRODUCTO.items() if k != "tlp"}
    with pytest.raises(ValueError, match="tlp"):
        build(sin_tlp)
    with pytest.raises(ValueError, match="tlp"):
        build({**PRODUCTO, "tlp": "   "})


def test_with_nothing_to_share_it_fails():
    vacio = {k: v for k, v in PRODUCTO.items() if k not in ("observables", "indicators", "malware")}
    with pytest.raises(ValueError, match="nothing to share"):
        build(vacio)


def test_an_unknown_marking_fails():
    with pytest.raises(ValueError):
        marking_object("violeta")


def test_an_unsupported_observable_type_fails():
    with pytest.raises(ValueError, match="unsupported"):
        build({**PRODUCTO, "observables": [{"type": "x-custom", "value": "x"}]})


def test_the_chain_lands_in_external_references():
    b = build(PRODUCTO, trace={"pir": "PIR-001", "assessment": "nightjar-vs-saltwind", "hunt": "HUNT-001"})
    report = next(o for o in b["objects"] if o["type"] == "report")
    assert report["external_references"] == [
        {"source_name": "cti-suite:pir", "external_id": "PIR-001"},
        {"source_name": "cti-suite:assessment", "external_id": "nightjar-vs-saltwind"},
        {"source_name": "cti-suite:hunt", "external_id": "HUNT-001"},
    ]


def test_without_a_chain_no_references_are_invented():
    report = next(o for o in build(PRODUCTO)["objects"] if o["type"] == "report")
    assert "external_references" not in report


def test_valid_until_is_emitted_and_checked():
    indicadores = [{**PRODUCTO["indicators"][0], "valid_until": "2027-01-01T00:00:00Z"}]
    b = build({**PRODUCTO, "indicators": indicadores})
    indicator = next(o for o in b["objects"] if o["type"] == "indicator")
    assert indicator["valid_until"] == "2027-01-01T00:00:00.000Z"

    with pytest.raises(ValueError, match="valid_until"):
        build({**PRODUCTO, "indicators": [{**PRODUCTO["indicators"][0], "valid_until": "2020-01-01T00:00:00Z"}]})
