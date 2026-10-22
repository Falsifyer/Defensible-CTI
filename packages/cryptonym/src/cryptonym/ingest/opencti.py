"""Ingest an existing actor (and its aliases) from OpenCTI.

Cryptonym does not replace OpenCTI; it reads an actor and writes graded linkages back.
This adapter covers the read direction and, like the others, emits one designation per
name so the alias list does not become an identity claim by accident.
"""

from __future__ import annotations

from typing import Any

from cryptonym.model.designation import Designation


def designations_from_opencti_actor(actor: dict[str, Any]) -> list[Designation]:
    """Map an OpenCTI actor dict into one designation per name."""
    name = actor.get("name")
    if not name:
        raise ValueError("OpenCTI actor is missing its 'name'")
    vendor = actor.get("createdBy") or actor.get("created_by") or "opencti"
    date = str(actor.get("created", ""))[:10]
    names = [name, *actor.get("aliases", [])]
    return [
        Designation(vendor=str(vendor), name=value, date=date)
        for value in names
        if value
    ]
