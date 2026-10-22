"""Evidence items, typed by whether they can actually distinguish two actors.

The central method rule: shared tradecraft is **non-diagnostic** for identity. Two
actors can use the same tooling, the same living-off-the-land binaries and the same
C2 paths without being the same organisational unit, so TTP overlap must not, on its
own, sustain a merge. Only distinguishing evidence — infrastructure, code or operator
artefacts — can.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class EvidenceType(StrEnum):
    """Category of an evidence item, which determines its diagnostic strength."""

    INFRASTRUCTURE = "infrastructure"
    CODE = "code"
    OPERATOR = "operator"
    TACTICS = "tactics"  # shared TTP — non-diagnostic for identity
    LINGUISTIC = "linguistic"  # vendor wording, structural cues
    STRUCTURAL = "structural"  # taxonomy / relationship shape
    OPEN_SOURCE = "open_source"  # reporting that does not fit the above


#: Evidence types that can, on their own, distinguish one actor from another.
DIAGNOSTIC_TYPES = frozenset({EvidenceType.INFRASTRUCTURE, EvidenceType.CODE, EvidenceType.OPERATOR})


class Consistency(StrEnum):
    """How an item of evidence sits against one hypothesis (ACH convention)."""

    CONSISTENT = "C"
    INCONSISTENT = "I"
    NEUTRAL = "0"


@dataclass(frozen=True)
class Evidence:
    """One item of evidence, with its consistency against each hypothesis.

    ``consistency`` is keyed by hypothesis value (e.g. ``"same_actor"``) so the model
    does not depend on the assessment module. A missing key is treated as neutral.
    """

    id: str
    statement: str
    source: str
    type: EvidenceType
    consistency: dict[str, Consistency] = field(default_factory=dict)

    @property
    def diagnostic(self) -> bool:
        """True when this type of evidence can discriminate between actors."""
        return self.type in DIAGNOSTIC_TYPES

    def is_discriminating(self) -> bool:
        """True when the item is not consistent with every hypothesis it addresses.

        Non-diagnostic overlap that is consistent with every hypothesis tells us
        nothing about identity — which is exactly why it must not close a merge.
        """
        values = set(self.consistency.values())
        return bool(values) and values != {Consistency.CONSISTENT}
