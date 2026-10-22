"""A dossier's source registry: who said it, and who is repeating whom.

The grade ceiling needs to know how many **independent** voices contributed diagnostic
evidence. Counting the `source` string was a proxy: two reports from one vendor with
different titles, or one vendor quoting another, counted as two. This module models the
sources themselves, so independence is structural and not typographic.

`derived_from` is the same relation the external-truth filter already uses: a source that
derives from another present is not a second voice.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SourceRef:
    """One source in a dossier's registry."""

    id: str
    publisher: str = ""
    url: str = ""
    derived_from: tuple[str, ...] = ()
    reliability: str = ""  # Admiralty reliability band, A-F

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SourceRef:
        return cls(
            id=str(data["id"]),
            publisher=str(data.get("publisher", "")),
            url=str(data.get("url", "")),
            derived_from=tuple(str(item) for item in data.get("derived_from", [])),
            reliability=str(data.get("reliability", "")).upper(),
        )


def registry(source_items: list[Any] | None) -> dict[str, SourceRef]:
    """Build ``{id: Source}`` from the dossier's ``sources`` list."""
    found: dict[str, SourceRef] = {}
    for item in source_items or []:
        if isinstance(item, SourceRef):
            found[item.id] = item
        elif isinstance(item, dict) and item.get("id"):
            found[str(item["id"])] = SourceRef.from_dict(item)
    return found


def independent_ids(ids: list[str], sources: dict[str, SourceRef]) -> list[str]:
    """Keep one voice per source, dropping any source derived from another that is present.

    Mirrors :func:`cti_method.adjudication.independent_sources`, one level down: here the
    question is how many independent voices contributed evidence, not how many asserted a
    truth.
    """
    present = set(ids)
    kept: list[str] = []
    seen_publishers: set[str] = set()
    for source_id in ids:
        source = sources.get(source_id)
        if source is None:
            # Unknown source: it has no declared derivation, so it stands on its own.
            if source_id not in kept:
                kept.append(source_id)
            continue
        if set(source.derived_from) & present:
            continue
        publisher = source.publisher.strip().lower()
        if publisher and publisher in seen_publishers:
            continue
        if publisher:
            seen_publishers.add(publisher)
        if source_id not in kept:
            kept.append(source_id)
    return kept


@dataclass(frozen=True)
class SourceKey:
    """How one evidence item is attributed: by registry id when present, by text otherwise."""

    key: str
    registered: bool
    derived_from: tuple[str, ...] = field(default_factory=tuple)


def attribute(source: str, source_id: str, sources: dict[str, SourceRef]) -> SourceKey:
    """Resolve an evidence item to the voice it represents."""
    if source_id and source_id in sources:
        entry = sources[source_id]
        return SourceKey(key=source_id, registered=True, derived_from=entry.derived_from)
    if source_id:
        return SourceKey(key=source_id, registered=False)
    return SourceKey(key=" ".join((source or "").lower().split()), registered=False)
