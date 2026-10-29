"""The external corpus scaffold must be valid before anyone collects a case."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cryptonym.evaluate.adjudication import validate_corpus

EXTERNAL = Path(__file__).resolve().parents[1] / "evaluation" / "external"


def _load(name: str) -> dict:
    return json.loads((EXTERNAL / name).read_text(encoding="utf-8"))


def test_the_protocol_has_the_gates_that_make_a_case_external() -> None:
    text = (EXTERNAL / "PROTOCOL.md").read_text(encoding="utf-8")
    for heading in ("Roles and independence", "Blindness", "Source independence", "Pre-registration"):
        assert heading in text


def test_the_schema_is_a_valid_draft_2020_12_schema() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    schema = _load("schema.json")
    jsonschema.Draft202012Validator.check_schema(schema)
    assert schema["$id"].endswith(
        "/packages/cryptonym/evaluation/external/schema.json"
    )


def test_the_template_is_valid_and_is_not_a_real_case() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    schema = _load("schema.json")
    template = _load("case.template.json")
    document = {
        "corpus": "external",
        "schema_version": "1.0",
        "protocol_version": "1.0",
        "cases": [template],
    }
    jsonschema.Draft202012Validator(schema).validate(document)
    assert template["_note"].startswith("TEMPLATE")
    assert template["id"] == "REPLACE-ME"
    assert template["adjudication"]["truth"] == "unadjudicated"


def test_the_template_passes_the_adjudication_filter_as_unadjudicated() -> None:
    template = _load("case.template.json")
    assert validate_corpus({"cases": [template]}) == []


def _run_validator(tmp_path: Path, document: dict) -> tuple[int, dict]:
    import json
    import subprocess
    import sys

    path = tmp_path / "corpus.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    result = subprocess.run(  # noqa: S603 - fixed script path
        [sys.executable, str(EXTERNAL / "validate_external.py"), str(path), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode, json.loads(result.stdout)


def _valid_corpus() -> dict:
    return {
        "corpus": "external",
        "schema_version": "1.0",
        "protocol_version": "1.0",
        "cases": [
            {
                "id": "case-1",
                "split": "development",
                "question": "Are A and B the same actor?",
                "subjects": [{"vendor": "Vendor A", "name": "A"}, {"vendor": "Vendor B", "name": "B"}],
                "judgement": {"confidence": "moderate"},
                "evidence": [
                    {
                        "id": "E1",
                        "statement": "one unique loader",
                        "source": "A",
                        "source_id": "s1",
                        "type": "code",
                        "consistency": {"same_actor": "C", "distinct_but_overlapping": "I"},
                    }
                ],
                "sources": [
                    {
                        "id": "s1",
                        "publisher": "A",
                        "url": "https://a.example/source",
                        "category": "vendor",
                        "kind": "asserts-same",
                    }
                ],
                "adjudication": {
                    "truth": "same_actor",
                    "standard": "independent-corroboration",
                    "adjudicators": ["Reviewer One", "Reviewer Two"],
                    "decided_at": "2026-01-01",
                    "sources": [
                        {
                            "publisher": "A",
                            "url": "https://a.example/source",
                            "category": "vendor",
                            "kind": "asserts-same",
                        },
                        {
                            "publisher": "B",
                            "url": "https://b.example/source",
                            "category": "vendor",
                            "kind": "asserts-same",
                        },
                    ],
                },
            }
        ],
    }


def test_the_validator_accepts_a_complete_external_case(tmp_path: Path) -> None:
    code, payload = _run_validator(tmp_path, _valid_corpus())
    assert code == 0, payload
    assert payload["valid"] is True


def test_the_validator_rejects_one_adjudicator_for_a_binary_truth(tmp_path: Path) -> None:
    document = _valid_corpus()
    document["cases"][0]["adjudication"]["adjudicators"] = ["Reviewer One"]
    code, payload = _run_validator(tmp_path, document)
    assert code == 1
    assert "binary-adjudicators" in {item["code"] for item in payload["findings"]}


def test_the_validator_rejects_a_derived_second_source(tmp_path: Path) -> None:
    document = _valid_corpus()
    document["cases"][0]["adjudication"]["sources"][1]["derived_from"] = ["A"]
    code, payload = _run_validator(tmp_path, document)
    assert code == 1
    assert "binary-not-earned" in {item["code"] for item in payload["findings"]}


def test_the_validator_rejects_the_template(tmp_path: Path) -> None:
    template = _load("case.template.json")
    code, payload = _run_validator(
        tmp_path,
        {
            "corpus": "external",
            "schema_version": "1.0",
            "protocol_version": "1.0",
            "cases": [template],
        },
    )
    assert code == 1
    assert "placeholder" in {item["code"] for item in payload["findings"]}


def test_the_validator_returns_two_for_broken_json(tmp_path: Path) -> None:
    import subprocess
    import sys

    path = tmp_path / "broken.json"
    path.write_text("{", encoding="utf-8")
    result = subprocess.run(  # noqa: S603 - fixed script path
        [sys.executable, str(EXTERNAL / "validate_external.py"), str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
