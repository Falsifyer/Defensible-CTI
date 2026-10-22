"""The schemas are the contract; the shipped documents must satisfy them."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest
from cti_method import schema as schemas

ROOT = Path(__file__).resolve().parents[3]


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "document,schema",
    [
        ("demo/pir.json", "pir"),
        ("demo/assessment.json", "assessment"),
        ("demo/hunt.json", "huntplan"),
        ("demo/product.json", "product"),
        ("packages/stixforge/examples/product.json", "product"),
    ],
)
def test_the_shipped_documents_match_their_schema(document: str, schema: str) -> None:
    schemas.validate(_load(ROOT / document), schema)


def test_the_schemas_travel_with_the_package() -> None:
    directory = schemas.directory()
    for name in schemas.NAMES:
        assert (directory / f"{name}.schema.json").is_file(), name


def test_a_claim_with_no_grade_is_not_a_valid_document() -> None:
    document = _load(ROOT / "demo/assessment.json")
    document.pop("judgement")
    with pytest.raises(jsonschema.ValidationError):
        schemas.validate(document, "assessment")


def test_one_hypothesis_is_not_a_valid_document() -> None:
    document = _load(ROOT / "demo/assessment.json")
    document["hypotheses"] = ["same_actor"]
    with pytest.raises(jsonschema.ValidationError):
        schemas.validate(document, "assessment")


def test_a_hypothesis_without_a_closure_is_not_a_valid_plan() -> None:
    document = _load(ROOT / "demo/hunt.json")
    document.pop("closure")
    with pytest.raises(jsonschema.ValidationError):
        schemas.validate(document, "huntplan")


def test_every_input_declares_its_schema_and_version() -> None:
    for document in ("demo/pir.json", "demo/assessment.json", "demo/hunt.json", "demo/product.json"):
        data = _load(ROOT / document)
        assert data["$schema"].endswith(".schema.json"), document
        assert data["schema_version"] == "1.0", document


def test_a_judgement_validates_against_the_judgement_schema() -> None:
    judgement = {
        "$schema": "https://github.com/ME0094/cti-suite/schemas/judgement.schema.json",
        "schema_version": "1.0",
        "question": "same?",
        "ranking": ["same_actor", "distinct"],
        "ceiling": "moderate",
        "confidence": "low",
        "grade_supported": True,
        "grade_findings": [],
    }
    schemas.validate(judgement, "judgement")


def test_the_judgement_schema_accepts_the_cryptonym_shape() -> None:
    schemas.validate(
        {"hypotheses_favoured": ["a"], "ceiling": "low", "grade_findings": []},
        "judgement",
    )


def test_a_ledger_entry_validates_against_its_schema(tmp_path: Path) -> None:
    from assessment.core import append_claim

    path = tmp_path / "ledger.jsonl"
    append_claim(str(path), {"id": "c1"}, now="2026-10-22T00:00:00Z")
    entry = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    schemas.validate(entry, "ledger-entry")
