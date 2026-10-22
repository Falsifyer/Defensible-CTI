"""Independent adjudication: what counts as external truth, and what to do on disagreement.

A corpus is only as honest as its truth. A truth asserted by this project is not
evidence; a single source is not corroboration; and a genuine disagreement between
sources is not a side to pick. This module encodes that as an **executable filter**, so
a case can only enter the accuracy figures if its adjudication earns it.

Three rules:

1. **External truth only.** A binary truth (same / distinct) must be established by
   sources, not by the author. ``author-assertion`` and ``single-source`` never qualify.
2. **Independence.** Two sources that derive from one another are one voice. A source
   that declares ``derived_from`` another present in the case does not count again.
3. **Disagreement is a result, not a round to win.** A hard conflict (some source
   asserts same, another asserts distinct) is ``contested`` and is excluded from the
   error rates. A scope dissent (a source that stops at overlap while another asserts
   identity) downgrades an *uncorroborated* claim to ``contested``.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import IntEnum, StrEnum
from typing import Any


class Truth(StrEnum):
    """The adjudicated relation between two designations."""

    SAME_ACTOR = "same_actor"
    DISTINCT = "distinct"
    CONTESTED = "contested"  # sources disagree, or scope is unresolved
    UNADJUDICATED = "unadjudicated"  # too thin, or no independent source asserts a stance

    @property
    def is_binary(self) -> bool:
        return self in (Truth.SAME_ACTOR, Truth.DISTINCT)


CLASSES = (Truth.SAME_ACTOR, Truth.DISTINCT)


class SourceCategory(StrEnum):
    GOVERNMENT = "government"
    VENDOR = "vendor"
    COMMUNITY = "community"
    OSINT = "osint"


class SourceKind(StrEnum):
    ASSERTS_SAME = "asserts-same"
    ASSERTS_DISTINCT = "asserts-distinct"
    OVERLAP = "overlap"  # observes overlap without asserting identity
    SILENT = "silent"


class Standard(IntEnum):
    """How a binary truth was established, weakest to strongest."""

    AUTHOR_ASSERTION = 0
    SINGLE_SOURCE = 1
    VENDOR_CONSENSUS = 2
    GOVERNMENT_STATEMENT = 3
    INDEPENDENT_CORROBORATION = 4


_STANDARD_BY_NAME = {
    "author-assertion": Standard.AUTHOR_ASSERTION,
    "single-source": Standard.SINGLE_SOURCE,
    "vendor-consensus": Standard.VENDOR_CONSENSUS,
    "government-statement": Standard.GOVERNMENT_STATEMENT,
    "independent-corroboration": Standard.INDEPENDENT_CORROBORATION,
}

#: The minimum number of independent sources a standard requires. ``government-statement``
#: still needs corroboration: a government name-list alone does not settle a disputed alias.
_MIN_INDEPENDENT = {
    Standard.VENDOR_CONSENSUS: 2,
    Standard.INDEPENDENT_CORROBORATION: 2,
}


def parse_standard(value: str | Standard | None) -> Standard | None:
    if value is None or isinstance(value, Standard):
        return value
    key = str(value).strip().lower()
    if key not in _STANDARD_BY_NAME:
        raise ValueError(f"unknown standard {value!r}; expected one of: {', '.join(_STANDARD_BY_NAME)}")
    return _STANDARD_BY_NAME[key]


@dataclass(frozen=True)
class Source:
    publisher: str
    url: str
    category: SourceCategory
    kind: SourceKind
    derived_from: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Source:
        return cls(
            publisher=data["publisher"],
            url=data.get("url", ""),
            category=SourceCategory(data["category"]),
            kind=SourceKind(data["kind"]),
            derived_from=tuple(data.get("derived_from", [])),
        )


@dataclass(frozen=True)
class Adjudication:
    truth: Truth
    standard: Standard | None = None
    sources: tuple[Source, ...] = ()
    adjudicators: tuple[str, ...] = ()
    disagreements: tuple[str, ...] = ()
    decided_at: str = ""
    note: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Adjudication:
        return cls(
            truth=Truth(data["truth"]),
            standard=parse_standard(data.get("standard")),
            sources=tuple(Source.from_dict(source) for source in data.get("sources", [])),
            adjudicators=tuple(data.get("adjudicators", [])),
            disagreements=tuple(data.get("disagreements", [])),
            decided_at=data.get("decided_at", ""),
            note=data.get("note", ""),
        )


@dataclass(frozen=True)
class Admissibility:
    declared_truth: Truth
    effective_truth: Truth
    admissible: bool
    standard: Standard | None
    independent_sources: int
    reasons: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, Any]:
        return {
            "declared_truth": self.declared_truth.value,
            "effective_truth": self.effective_truth.value,
            "admissible": self.admissible,
            "standard": self.standard.name.lower() if self.standard else None,
            "independent_sources": self.independent_sources,
            "reasons": list(self.reasons),
        }


def independent_sources(sources: Iterable[Source]) -> list[Source]:
    """Keep one voice per publisher, and drop any source that derives from another present.

    Two outlets repeating one origin are one voice; so are two documents from the same
    publisher. Neither is corroboration.
    """
    sources = list(sources)
    present = {source.publisher for source in sources}
    seen: set[str] = set()
    result: list[Source] = []
    for source in sources:
        if set(source.derived_from) & present:
            continue
        key = source.publisher.strip().lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(source)
    return result


def _verdict(
    declared: Truth, effective: Truth, admissible: bool, standard: Standard | None, independent: int, *reasons: str
) -> Admissibility:
    return Admissibility(
        declared_truth=declared,
        effective_truth=effective,
        admissible=admissible,
        standard=standard,
        independent_sources=independent,
        reasons=reasons,
    )


def filter_adjudication(adjudication: Adjudication) -> Admissibility:
    """Apply the external-truth filter and return the effective, usable truth."""
    truth = adjudication.truth
    standard = adjudication.standard
    independent = independent_sources(adjudication.sources)

    # A truth already recorded as contested/unadjudicated is never a binary result.
    if not truth.is_binary:
        return _verdict(truth, truth, False, standard, len(independent), f"adjudicated as {truth.value}")

    # 1. A binary truth needs a declared standard of evidence.
    if standard is None:
        return _verdict(truth, Truth.UNADJUDICATED, False, None, len(independent), "binary truth without a standard")

    # 2. Hard conflict: independent sources directly disagree -> contested.
    asserts_same = any(source.kind is SourceKind.ASSERTS_SAME for source in independent)
    asserts_distinct = any(source.kind is SourceKind.ASSERTS_DISTINCT for source in independent)
    if asserts_same and asserts_distinct:
        return _verdict(
            truth,
            Truth.CONTESTED,
            False,
            standard,
            len(independent),
            "independent sources assert both same and distinct",
        )

    # 3. The standard must be earned.
    if standard in (Standard.AUTHOR_ASSERTION, Standard.SINGLE_SOURCE):
        return _verdict(
            truth,
            Truth.UNADJUDICATED,
            False,
            standard,
            len(independent),
            f"{standard.name.lower()} is not external truth",
        )
    if standard is Standard.GOVERNMENT_STATEMENT:
        government = any(
            source.category is SourceCategory.GOVERNMENT
            and source.kind in (SourceKind.ASSERTS_SAME, SourceKind.ASSERTS_DISTINCT)
            for source in independent
        )
        if not government or len(independent) < 2:
            return _verdict(
                truth,
                Truth.UNADJUDICATED,
                False,
                standard,
                len(independent),
                "government statement needs an independent corroborating source",
            )
    else:
        minimum = _MIN_INDEPENDENT.get(standard, 2)
        if len(independent) < minimum:
            return _verdict(
                truth,
                Truth.UNADJUDICATED,
                False,
                standard,
                len(independent),
                f"{standard.name.lower()} needs >= {minimum} independent sources, found {len(independent)}",
            )

    # 4. Something must actually assert the declared direction.
    asserted_kind = SourceKind.ASSERTS_SAME if truth is Truth.SAME_ACTOR else SourceKind.ASSERTS_DISTINCT
    corroborators = [source for source in independent if source.kind is asserted_kind]
    if not corroborators:
        return _verdict(
            truth,
            Truth.UNADJUDICATED,
            False,
            standard,
            len(independent),
            f"no independent source asserts {truth.value}",
        )

    # 5. Scope dissent: a source that stops at overlap downgrades an uncorroborated claim.
    dissenters = [source for source in independent if source.kind is SourceKind.OVERLAP]
    if dissenters and len(corroborators) < 2:
        return _verdict(
            truth,
            Truth.CONTESTED,
            False,
            standard,
            len(independent),
            "scope dissent (overlap) without corroboration of the binary claim",
        )

    reasons = ()
    if dissenters:
        reasons = ("scope dissent noted; binary claim corroborated by >= 2 independent sources",)
    return _verdict(truth, truth, True, standard, len(independent), *reasons)


def validate_corpus(document: dict[str, Any]) -> list[str]:
    """Return the problems that make a corpus invalid (empty means valid)."""
    problems: list[str] = []
    seen: set[str] = set()
    cases = document.get("cases", [])
    if not cases:
        problems.append("corpus has no cases")
    for index, case in enumerate(cases):
        where = case.get("id", f"#{index}")
        if "id" not in case:
            problems.append(f"{where}: missing id")
        elif case["id"] in seen:
            problems.append(f"{where}: duplicate id")
        else:
            seen.add(case["id"])
        if "question" not in case:
            problems.append(f"{where}: missing question")
        if "evidence" not in case:
            problems.append(f"{where}: missing evidence")
        if "adjudication" not in case:
            problems.append(f"{where}: missing adjudication")
            continue
        try:
            adjudication = Adjudication.from_dict(case["adjudication"])
        except (KeyError, ValueError) as exc:
            problems.append(f"{where}: invalid adjudication ({type(exc).__name__}: {exc})")
            continue
        if adjudication.truth.is_binary and adjudication.standard is None:
            problems.append(f"{where}: binary truth requires a standard")
        for source in adjudication.sources:
            if source.url and not source.url.startswith(("http://", "https://")):
                problems.append(f"{where}: source {source.publisher} has a non-URL url")
    return problems
