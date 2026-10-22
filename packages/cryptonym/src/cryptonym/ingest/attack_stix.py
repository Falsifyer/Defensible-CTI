"""Ingest MITRE ATT&CK intrusion sets and their aliases from STIX.

ATT&CK records tracking names as **Associated Groups** — explicitly weaker than "same
actor". The adapter keeps the weakness visible: it emits each name as a separate
designation instead of flattening the alias list into a single identity.
"""

from __future__ import annotations

from typing import Any

from cryptonym.model.designation import Designation


def designations_from_attack_bundle(bundle: dict[str, Any]) -> list[Designation]:
    """Map an ATT&CK STIX bundle's ``intrusion-set`` objects into designations."""
    designations: list[Designation] = []
    for obj in bundle.get("objects", []):
        if obj.get("type") != "intrusion-set":
            continue
        date = str(obj.get("modified", ""))[:10]
        names = [obj.get("name", ""), *obj.get("aliases", [])]
        for name in names:
            if name:
                designations.append(Designation(vendor="mitre-attack", name=name, date=date))
    return designations
