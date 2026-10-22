"""The schemas are the contract; the demo documents must satisfy them."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[3]
SCHEMAS = ROOT / "schemas"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "document,schema",
    [
        ("demo/pir.json", "pir.schema.json"),
        ("demo/assessment.json", "assessment.schema.json"),
        ("demo/hunt.json", "huntplan.schema.json"),
        ("demo/product.json", "product.schema.json"),
        ("packages/stixforge/examples/product.json", "product.schema.json"),
    ],
)
def test_the_shipped_documents_match_their_schema(document: str, schema: str) -> None:
    jsonschema.Draft202012Validator(_load(SCHEMAS / schema)).validate(_load(ROOT / document))


def test_a_claim_with_no_grade_is_not_a_valid_document() -> None:
    document = _load(ROOT / "demo/assessment.json")
    document.pop("judgement")
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(_load(SCHEMAS / "assessment.schema.json")).validate(document)


def test_one_hypothesis_is_not_a_valid_document() -> None:
    document = _load(ROOT / "demo/assessment.json")
    document["hypotheses"] = ["same_actor"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(_load(SCHEMAS / "assessment.schema.json")).validate(document)


def test_a_hypothesis_without_a_closure_is_not_a_valid_plan() -> None:
    document = _load(ROOT / "demo/hunt.json")
    document.pop("closure")
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(_load(SCHEMAS / "huntplan.schema.json")).validate(document)


def test_every_document_declares_its_schema_and_version() -> None:
    for document in ("demo/pir.json", "demo/assessment.json", "demo/hunt.json", "demo/product.json"):
        data = _load(ROOT / document)
        assert data["$schema"].endswith(".schema.json"), document
        assert data["schema_version"] == "1.0", document
