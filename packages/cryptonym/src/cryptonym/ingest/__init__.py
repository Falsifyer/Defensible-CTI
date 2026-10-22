"""Ingest adapters: map external sources of designations into Cryptonym's model.

They are deliberately thin, operate on already-parsed dicts, and never make a network
call on their own. The whole point of ingest is to keep the names **apart** that a
source stores as one flat list, so a linkage between them can be graded rather than
assumed.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cryptonym.config import SUPPORTED_SOURCES
from cryptonym.ingest.attack_stix import designations_from_attack_bundle
from cryptonym.ingest.misp_galaxy import designations_from_galaxies
from cryptonym.ingest.opencti import designations_from_opencti_actor
from cryptonym.model.designation import Designation


def validate_source(source: str) -> None:
    """Fail closed on an unknown source before any I/O."""
    if source not in SUPPORTED_SOURCES:
        raise ValueError(f"unsupported source: {source}; expected one of: {', '.join(SUPPORTED_SOURCES)}")


def from_document(source: str, data: Any) -> list[Designation]:
    """Map an already-parsed source document into designations."""
    validate_source(source)
    if source == "misp-galaxy":
        clusters = data.get("values", [data]) if isinstance(data, dict) else data
        return designations_from_galaxies(clusters)
    if source == "attack-stix":
        return designations_from_attack_bundle(data)
    return designations_from_opencti_actor(data)


def load(source: str, path: str | Path) -> list[Designation]:
    """Load designations from a local JSON document for the given source."""
    validate_source(source)
    return from_document(source, json.loads(Path(path).read_text(encoding="utf-8")))
