"""Tests for the STIX / MISP / TAXII exporters."""

from __future__ import annotations

from cryptonym.export.misp_galaxy import to_misp_galaxy_cluster
from cryptonym.export.stix_bundle import to_stix_bundle, to_stix_objects
from cryptonym.export.taxii import to_taxii_envelope
from cryptonym.model.assessment import Assessment
from cryptonym.model.confidence import Confidence, Judgement
from cryptonym.model.designation import Designation
from cryptonym.model.evidence import Consistency, Evidence, EvidenceType
from cryptonym.reconcile.graph import Linkage, Reconciliation

STAMP = "2026-10-09T00:00:00Z"


def _assessment() -> Assessment:
    return Assessment(
        id="voltzite-vs-volt-typhoon",
        question="Is VOLTZITE the same actor as Volt Typhoon?",
        subjects=[Designation("Dragos", "VOLTZITE"), Designation("Microsoft", "Volt Typhoon")],
        evidence=[
            Evidence(
                id="E1",
                statement="overlap wording",
                source="vendor",
                type=EvidenceType.LINGUISTIC,
                consistency={"same_actor": Consistency.INCONSISTENT},
            )
        ],
        judgement=Judgement(confidence=Confidence.MODERATE),
        version="1.0",
    )


def _reconciliation() -> Reconciliation:
    return Reconciliation(
        linkages=[Linkage("Dragos:VOLTZITE", "Microsoft:Volt Typhoon", Confidence.MODERATE, "vh-2026")]
    )


def test_stix_bundle_wraps_designations_and_linkages() -> None:
    bundle = to_stix_bundle(_assessment(), _reconciliation(), timestamp=STAMP)
    assert bundle["type"] == "bundle"
    types = [obj["type"] for obj in bundle["objects"]]
    assert types.count("x-cryptonym-designation") == 2
    assert types.count("x-cryptonym-linkage") == 1


def test_stix_ids_are_deterministic() -> None:
    first = to_stix_objects(_assessment(), _reconciliation(), timestamp=STAMP)
    second = to_stix_objects(_assessment(), _reconciliation(), timestamp=STAMP)
    assert [obj["id"] for obj in first] == [obj["id"] for obj in second]


def test_stix_linkage_keeps_confidence_and_provenance() -> None:
    objects = to_stix_objects(_assessment(), _reconciliation(), timestamp=STAMP)
    linkage = next(obj for obj in objects if obj["type"] == "x-cryptonym-linkage")
    assert linkage["confidence"] == "moderate"
    assert linkage["assessment_id"] == "vh-2026"
    assert linkage["left_ref"] and linkage["right_ref"]


def test_misp_cluster_is_assessed_not_asserted() -> None:
    cluster = to_misp_galaxy_cluster(_assessment(), _reconciliation())
    assert cluster["aliases_assessed_not_asserted"] is True
    assert cluster["values"][0]["meta"]["cryptonym:confidence"] == "moderate"
    assert cluster["meta"]["cryptonym:linkages"][0]["confidence"] == "moderate"


def test_taxii_envelope_carries_the_objects() -> None:
    envelope = to_taxii_envelope(_assessment(), _reconciliation(), timestamp=STAMP)
    assert envelope["more"] is False
    assert any(obj["type"] == "x-cryptonym-linkage" for obj in envelope["objects"])
