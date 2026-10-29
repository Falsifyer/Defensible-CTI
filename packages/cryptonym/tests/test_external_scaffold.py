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
