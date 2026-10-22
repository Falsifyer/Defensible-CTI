"""A designation is a vendor's name for activity — not a claim about identity."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Designation:
    """One vendor's tracking name for a cluster of activity.

    Cryptonym never assumes two designations are the same actor; it records them
    separately and grades the *linkage* between them elsewhere.
    """

    vendor: str
    name: str
    source_url: str = ""
    date: str = ""
    tlp: str = "TLP:WHITE"

    def __post_init__(self) -> None:
        if not self.vendor or not self.name:
            raise ValueError("a designation requires both a vendor and a name")

    @property
    def key(self) -> str:
        """Stable identity of the designation itself (vendor-scoped, not global)."""
        return f"{self.vendor}:{self.name}"
