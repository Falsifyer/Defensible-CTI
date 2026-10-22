"""Ingest designations and aliases from MISP Galaxy threat-actor clusters.

MISP stores a threat actor as one cluster with its aliases flattened into a synonym
list. Cryptonym reads those clusters and turns **each** name into its own ``Designation``
— the names stay apart, and whether they are the same actor becomes a graded linkage
rather than a given.
"""

from __future__ import annotations

from typing import Any

from cryptonym.model.designation import Designation


def designations_from_galaxy(cluster: dict[str, Any]) -> list[Designation]:
    """Map one Galaxy cluster into one designation per name (canonical + synonyms)."""
    value = cluster.get("value")
    if not value:
        raise ValueError("galaxy cluster is missing its 'value'")
    meta = cluster.get("meta", {})
    names = [value, *meta.get("synonyms", [])]
    refs = meta.get("refs", [])
    source_url = refs[0] if refs else ""
    return [Designation(vendor="misp-galaxy", name=name, source_url=source_url) for name in names]


def designations_from_galaxies(clusters: list[dict[str, Any]]) -> list[Designation]:
    """Map many Galaxy clusters, de-duplicating identical designations."""
    seen: dict[str, Designation] = {}
    for cluster in clusters:
        for designation in designations_from_galaxy(cluster):
            seen.setdefault(designation.key, designation)
    return list(seen.values())
