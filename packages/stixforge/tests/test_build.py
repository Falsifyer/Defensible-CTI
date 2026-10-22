import json
from pathlib import Path

import pytest

from stixforge.build import build
from stixforge.markings import TLP, marking_object

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
PRODUCTO = json.loads((EXAMPLES / "product.json").read_text(encoding="utf-8"))


def test_el_bundle_tiene_marcado_identidad_y_reporte():
    b = build(PRODUCTO)
    tipos = [o["type"] for o in b["objects"]]
    assert b["type"] == "bundle"
    assert "marking-definition" in tipos
    assert "identity" in tipos
    assert "report" in tipos


def test_es_determinista_byte_a_byte():
    assert json.dumps(build(PRODUCTO)) == json.dumps(build(PRODUCTO))


def test_el_reporte_referencia_todo_lo_compartible():
    b = build(PRODUCTO)
    report = next(o for o in b["objects"] if o["type"] == "report")
    ids = {o["id"] for o in b["objects"]}
    assert report["object_refs"]
    assert set(report["object_refs"]) <= ids
    assert len(report["object_refs"]) == 5  # 2 observables + 2 indicadores + 1 malware


def test_todo_sdo_lleva_marcado_y_los_sco_no_lo_necesitan():
    b = build(PRODUCTO)
    sco = {"domain-name", "ipv4-addr", "ipv6-addr", "url", "file", "email-addr"}
    for o in b["objects"]:
        if o["type"] == "marking-definition" or o["type"] in sco:
            continue
        assert o["object_marking_refs"], o["id"]
    for o in b["objects"]:
        if o["type"] in sco:
            # En 2.1 un SCO no lleva created, modified, created_by_ref ni marcado.
            assert set(o) <= {"type", "spec_version", "id", "value", "hashes"}


def test_clear_usa_el_marcado_oficial_de_tlp_2_0():
    b = build({**PRODUCTO, "tlp": "clear"})
    marcado = next(o for o in b["objects"] if o["type"] == "marking-definition")
    assert marcado["id"] == TLP["CLEAR"]["id"]
    assert marcado["name"] == "TLP:CLEAR"
    assert marcado["extensions"]


def test_amber_estricto_existe_como_marcado_de_primera_clase():
    marcado = marking_object("amber+strict")
    assert marcado["id"] == TLP["AMBER+STRICT"]["id"]
    assert marcado["name"] == "TLP:AMBER+STRICT"


def test_white_esta_deprecado_y_no_se_emite():
    with pytest.raises(ValueError, match="deprecated"):
        marking_object("TLP:WHITE")


def test_el_ejemplo_va_en_amber():
    b = build(PRODUCTO)
    marcado = next(o for o in b["objects"] if o["type"] == "marking-definition")
    assert marcado["id"] == TLP["AMBER"]["id"]


def test_sin_created_falla_para_no_forjar_una_version_nueva_con_el_mismo_id():
    sin_fecha = {k: v for k, v in PRODUCTO.items() if k != "created"}
    with pytest.raises(ValueError, match="created"):
        build(sin_fecha)


def test_sin_titulo_falla():
    with pytest.raises(ValueError, match="title"):
        build({**PRODUCTO, "title": ""})


def test_sin_autor_falla():
    with pytest.raises(ValueError, match="author"):
        build({**PRODUCTO, "author": ""})


def test_sin_nada_que_compartir_falla():
    vacio = {k: v for k, v in PRODUCTO.items() if k not in ("observables", "indicators", "malware")}
    with pytest.raises(ValueError, match="nothing to share"):
        build(vacio)


def test_marcado_desconocido_falla():
    with pytest.raises(ValueError):
        marking_object("violeta")


def test_observable_de_tipo_no_soportado_falla():
    with pytest.raises(ValueError, match="unsupported"):
        build({**PRODUCTO, "observables": [{"type": "x-custom", "value": "x"}]})


def test_la_cadena_queda_en_external_references():
    b = build(PRODUCTO, trace={"pir": "PIR-001", "assessment": "nightjar-vs-saltwind", "hunt": "HUNT-001"})
    report = next(o for o in b["objects"] if o["type"] == "report")
    assert report["external_references"] == [
        {"source_name": "cti-suite:pir", "external_id": "PIR-001"},
        {"source_name": "cti-suite:assessment", "external_id": "nightjar-vs-saltwind"},
        {"source_name": "cti-suite:hunt", "external_id": "HUNT-001"},
    ]


def test_sin_cadena_no_se_inventan_referencias():
    report = next(o for o in build(PRODUCTO)["objects"] if o["type"] == "report")
    assert "external_references" not in report


def test_valid_until_se_emite_y_se_comprueba():
    indicadores = [{**PRODUCTO["indicators"][0], "valid_until": "2027-01-01T00:00:00Z"}]
    b = build({**PRODUCTO, "indicators": indicadores})
    indicador = next(o for o in b["objects"] if o["type"] == "indicator")
    assert indicador["valid_until"] == "2027-01-01T00:00:00Z"

    with pytest.raises(ValueError, match="valid_until"):
        build({**PRODUCTO, "indicators": [{**PRODUCTO["indicators"][0], "valid_until": "2020-01-01T00:00:00Z"}]})
