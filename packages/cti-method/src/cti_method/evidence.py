"""Evidence items, typed by whether they can actually distinguish two actors.

The central method rule: shared tradecraft is **non-diagnostic** for identity. Two
actors can use the same tooling, the same living-off-the-land binaries and the same
C2 paths without being the same organisational unit, so TTP overlap must not, on its
own, sustain a merge. Only distinguishing evidence — infrastructure, code or operator
artefacts — can.

An item may name its source in the dossier's registry (``source_id``) and carry an
Admiralty reliability band (``reliability``). Both are optional: a dossier without a
registry still works, it just cannot distinguish two reports from one vendor beyond the
source string.
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


#: Admiralty reliability -> weight in the ACH score. A is a source you would bet on; F is
#: one you cannot judge, which is not the same as worthless, so it keeps a middle weight.
RELIABILITY_WEIGHT: dict[str, float] = {
    "A": 1.0,
    "B": 0.8,
    "C": 0.6,
    "D": 0.4,
    "E": 0.2,
    "F": 0.5,
}
DEFAULT_WEIGHT = 1.0


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
    source_id: str = ""
    reliability: str = ""
    direct: bool = False

    @property
    def diagnostic(self) -> bool:
        """True when this type of evidence can discriminate between actors."""
        return self.type in DIAGNOSTIC_TYPES

    @property
    def weight(self) -> float:
        """Weight in the ACH score, from the Admiralty reliability band."""
        return RELIABILITY_WEIGHT.get((self.reliability or "").upper(), DEFAULT_WEIGHT)

    def is_discriminating(self) -> bool:
        """True when the item is not consistent with every hypothesis it addresses.

        Non-diagnostic overlap that is consistent with every hypothesis tells us
        nothing about identity — which is exactly why it must not close a merge.
        """
        values = set(self.consistency.values())
        return bool(values) and values != {Consistency.CONSISTENT}
