"""Conformance: the STIX Cryptonym emits is accepted by the official library.

Skipped when ``stix2`` is not installed. When it is (CI installs it as a dev
dependency), this proves the bundle is not just shaped like STIX but is STIX.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

stix2 = pytest.importorskip("stix2")

from cryptonym.export.stix_bundle import to_stix_bundle  # noqa: E402
from cryptonym.model.assessment import load_assessment  # noqa: E402
from cryptonym.model.confidence import Confidence  # noqa: E402
from cryptonym.reconcile.graph import Linkage, Reconciliation  # noqa: E402

DOSSIER = Path(__file__).resolve().parents[1] / "assessments" / "voltzite-vs-volt-typhoon" / "assessment.json"


def test_bundle_parses_with_the_official_library() -> None:
    assessment = load_assessment(DOSSIER)
    reconciliation = Reconciliation(
        [Linkage("Dragos:VOLTZITE", "Microsoft:Volt Typhoon", Confidence.MODERATE, "voltzite-vs-volt-typhoon")]
    )
    bundle = to_stix_bundle(assessment, reconciliation, timestamp="2026-10-09T00:00:00Z")
    parsed = stix2.parse(json.dumps(bundle), allow_custom=True)
    assert parsed.type == "bundle"
    types = [obj["type"] if isinstance(obj, dict) else obj.type for obj in parsed.objects]
    assert types.count("x-cryptonym-designation") == 2
    assert types.count("x-cryptonym-linkage") == 1
