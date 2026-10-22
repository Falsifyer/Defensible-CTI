"""Static configuration and shared constants."""

from __future__ import annotations

from cti_method.metrics import SPLITS

DEFAULT_TLP = "TLP:CLEAR"
DEFAULT_VERSION = "1.0"

#: Source adapters Cryptonym can ingest from. A source's names are stored **apart**, not
#: flattened into one identity.
SUPPORTED_SOURCES = ("misp-galaxy", "attack-stix", "opencti")

#: Shareable export formats. Every one preserves confidence and provenance.
EXPORT_FORMATS = ("stix", "misp", "taxii")

__all__ = ["DEFAULT_TLP", "DEFAULT_VERSION", "EXPORT_FORMATS", "SPLITS", "SUPPORTED_SOURCES"]
