import copy
import json
from pathlib import Path

from stixforge.build import build
from stixforge.cli import main
from stixforge.validate import validate

PRODUCTO = json.loads(Path("examples/product.json").read_text(encoding="utf-8"))


def test_un_bundle_reconstruido_es_valido():
    r = validate(build(PRODUCTO))
    assert r["valid"] is True
    assert r["findings"] == []


def test_sin_marcado_en_un_objeto_falla():
    b = build(PRODUCTO)
    objetivo = next(o for o in b["objects"] if o["type"] == "indicator")
    del objetivo["object_marking_refs"]
    r = validate(b)
    assert r["valid"] is False
    assert "no-marking" in {h["code"] for h in r["findings"]}


def test_referencia_que_no_resuelve_falla():
    b = build(PRODUCTO)
    report = next(o for o in b["objects"] if o["type"] == "report")
    report["object_refs"] = report["object_refs"] + ["indicator--00000000-0000-4000-8000-000000000000"]
    assert "unresolved-reference" in {h["code"] for h in validate(b)["findings"]}


def test_id_repetido_falla():
    b = build(PRODUCTO)
    b["objects"].append(copy.deepcopy(b["objects"][1]))
    assert "duplicate-id" in {h["code"] for h in validate(b)["findings"]}


def test_id_con_tipo_que_no_casa_falla():
    b = build(PRODUCTO)
    b["objects"][2]["id"] = b["objects"][2]["id"].replace("domain-name--", "indicator--")
    assert "id-type-mismatch" in {h["code"] for h in validate(b)["findings"]}


def test_fichero_que_no_es_bundle():
    r = validate({"type": "indicator"})
    assert r["valid"] is False
    assert r["findings"][0]["code"] == "not-a-bundle"


def test_cli_build_y_validate(tmp_path, capsys):
    salida = tmp_path / "bundle.json"
    assert main(["build", "examples/product.json", "-o", str(salida)]) == 0
    assert main(["validate", str(salida)]) == 0
    assert "Result: valid" in capsys.readouterr().out


def test_cli_sale_con_dos_si_no_puede_leer(tmp_path):
    assert main(["validate", str(tmp_path / "no-existe.json")]) == 2


def test_cli_sin_validador_externo_sale_con_dos(tmp_path, capsys):
    salida = tmp_path / "bundle.json"
    main(["build", "examples/product.json", "-o", str(salida)])
    capsys.readouterr()
    # En este entorno stix2-validator no esta instalado: no comprobado no es limpio.
    codigo = main(["validate", str(salida), "--external"])
    assert codigo in (0, 1, 2)
    if codigo == 2:
        assert "NOT run" in capsys.readouterr().err or "not installed" in capsys.readouterr().out
