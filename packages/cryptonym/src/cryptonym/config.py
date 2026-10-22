"""Static configuration and shared constants."""

from __future__ import annotations

DEFAULT_TLP = "TLP:WHITE"
DEFAULT_VERSION = "1.0"

#: Source adapters Cryptonym can ingest from. A source's names are stored **apart**, not
#: flattened into one identity.
SUPPORTED_SOURCES = ("misp-galaxy", "attack-stix", "opencti")

#: Shareable export formats. Every one preserves confidence and provenance.
EXPORT_FORMATS = ("stix", "misp", "taxii")

#: Evaluation splits. A method that is graded on cases it was tuned against proves
#: nothing, so results are always reported per split.
SPLITS = ("development", "held-out")
