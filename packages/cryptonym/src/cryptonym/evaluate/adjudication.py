"""Compatibility re-export: the adjudication filter lives in :mod:`cti_method.adjudication`.

External truth is not alias-specific: any corpus can declare a standard, sources and a
disagreement. The implementation moved to the shared core so ``assessment`` can use it
without importing the alias package.
"""

from __future__ import annotations

from cti_method.adjudication import (
    CLASSES,
    Adjudication,
    Admissibility,
    Source,
    SourceCategory,
    SourceKind,
    Standard,
    Truth,
    filter_adjudication,
    independent_sources,
    parse_standard,
    validate_corpus,
)

__all__ = [
    "CLASSES",
    "Admissibility",
    "Adjudication",
    "Source",
    "SourceCategory",
    "SourceKind",
    "Standard",
    "Truth",
    "filter_adjudication",
    "independent_sources",
    "parse_standard",
    "validate_corpus",
]
