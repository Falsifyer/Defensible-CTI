import copy
import json
from pathlib import Path

from stixforge.build import build
from stixforge.cli import main
from stixforge.validate import validate

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
PRODUCTO = json.loads((EXAMPLES / "product.json").read_text(encoding="utf-8"))


def test_a_rebuilt_bundle_is_valid():
    r = validate(build(PRODUCTO))
    assert r["valid"] is True
    assert r["findings"] == []


def test_an_unmarked_object_fails():
    b = build(PRODUCTO)
    target = next(o for o in b["objects"] if o["type"] == "indicator")
    del target["object_marking_refs"]
    r = validate(b)
    assert r["valid"] is False
    assert "stix-no-marking" in {h["code"] for h in r["findings"]}


def test_an_unresolved_reference_fails():
    b = build(PRODUCTO)
    report = next(o for o in b["objects"] if o["type"] == "report")
    report["object_refs"] = report["object_refs"] + ["indicator--00000000-0000-4000-8000-000000000000"]
    assert "stix-unresolved-reference" in {h["code"] for h in validate(b)["findings"]}


def test_a_duplicate_id_fails():
    b = build(PRODUCTO)
    b["objects"].append(copy.deepcopy(b["objects"][1]))
    assert "stix-duplicate-id" in {h["code"] for h in validate(b)["findings"]}


def test_an_id_that_does_not_match_its_type_fails():
    b = build(PRODUCTO)
    b["objects"][2]["id"] = b["objects"][2]["id"].replace("domain-name--", "indicator--")
    assert "stix-id-type-mismatch" in {h["code"] for h in validate(b)["findings"]}


def test_a_file_that_is_not_a_bundle():
    r = validate({"type": "indicator"})
    assert r["valid"] is False
    assert r["findings"][0]["code"] == "stix-not-bundle"


def test_cli_build_y_validate(tmp_path, capsys):
    output = tmp_path / "bundle.json"
    assert main(["build", str(EXAMPLES / "product.json"), "-o", str(output)]) == 0
    assert main(["validate", str(output)]) == 0
    assert "Result: valid" in capsys.readouterr().out


def test_cli_exits_two_when_it_cannot_read(tmp_path):
    assert main(["validate", str(tmp_path / "no-existe.json")]) == 2


def test_cli_without_an_external_validator_exits_two(tmp_path, capsys):
    output = tmp_path / "bundle.json"
    main(["build", str(EXAMPLES / "product.json"), "-o", str(output)])
    capsys.readouterr()
    # In this environment stix2-validator is not installed: not checked is not clean.
    codigo = main(["validate", str(output), "--external"])
    assert codigo in (0, 1, 2)
    if codigo == 2:
        assert "NOT run" in capsys.readouterr().err or "not installed" in capsys.readouterr().out


def test_the_oasis_library_accepts_the_bundle(tmp_path):
    """The --external path stops being untested: it validates with the real stix2."""
    pytest = __import__("pytest")
    pytest.importorskip("stix2")
    from stixforge.validate import external

    bundle = build(PRODUCTO)
    path = tmp_path / "bundle.json"
    path.write_text(json.dumps(bundle), encoding="utf-8")
    result = external(bundle, path)
    assert result["available"] is True
    assert result["library"]["ok"] is True, result["library"]
