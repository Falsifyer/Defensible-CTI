import json
from pathlib import Path

import pytest

from stixforge.build import build
from stixforge.markings import MARKINGS, marking_object

PRODUCTO = json.loads(Path("examples/product.json").read_text(encoding="utf-8"))


def test_el_bundle_tiene_marcado_identidad_y_reporte():
    b = build(PRODUCTO)
    tipos = [o["type"] for o in b["objects"]]
    assert b["type"] == "bundle"
    assert "marking-definition" in tipos
    assert "identity" in tipos
    assert "report" in tipos


def test_es_determinista():
    assert build(PRODUCTO) == build(PRODUCTO)


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


def test_clear_se_emite_con_el_marcado_de_la_especificacion():
    b = build({**PRODUCTO, "tlp": "clear"})
    marcado = next(o for o in b["objects"] if o["type"] == "marking-definition")
    assert marcado["id"] == MARKINGS["white"][0]
    assert marcado["name"] == "TLP:WHITE"


def test_el_ejemplo_va_en_amber():
    b = build(PRODUCTO)
    marcado = next(o for o in b["objects"] if o["type"] == "marking-definition")
    assert marcado["id"] == MARKINGS["amber"][0]


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
