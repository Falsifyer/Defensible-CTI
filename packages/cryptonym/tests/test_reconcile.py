"""Tests for graded reconciliation — clusters compute, merges do not stick."""

from __future__ import annotations

from cryptonym.model.confidence import Confidence
from cryptonym.reconcile.graph import Linkage, Reconciliation


def _graph() -> Reconciliation:
    return Reconciliation(
        linkages=[
            Linkage("MS:Volt Typhoon", "Dragos:VOLTZITE", Confidence.MODERATE, "vh-2026"),
            Linkage("Dragos:VOLTZITE", "Palo Alto:Insidious Taurus", Confidence.LOW, "vh-2026"),
        ]
    )


def test_cluster_at_moderate_threshold_excludes_low_link() -> None:
    clusters = _graph().clusters(Confidence.MODERATE)
    assert {frozenset(c) for c in clusters} == {frozenset({"MS:Volt Typhoon", "Dragos:VOLTZITE"})}


def test_cluster_at_low_threshold_joins_them() -> None:
    clusters = _graph().clusters(Confidence.LOW)
    assert any(len(cluster) == 3 for cluster in clusters)


def test_weakest_link_is_reported_not_averaged() -> None:
    cluster = {"MS:Volt Typhoon", "Dragos:VOLTZITE", "Palo Alto:Insidious Taurus"}
    weakest = _graph().weakest_link(cluster)
    assert weakest is not None
    assert weakest.confidence is Confidence.LOW


def test_weakest_link_is_none_without_internal_edges() -> None:
    assert _graph().weakest_link({"unknown:foo"}) is None
