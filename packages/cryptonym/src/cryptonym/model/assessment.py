"""An assessment: the graded, versioned judgement linking two designations."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from cti_method.confidence import Confidence, Judgement, parse_confidence, parse_probability
from cti_method.evidence import Consistency, Evidence, EvidenceType

from cryptonym.model.designation import Designation

DEFAULT_TLP = "TLP:CLEAR"


class Hypothesis(StrEnum):
    """The competing explanations tested against the evidence."""

    SAME = "same_actor"
    OVERLAPPING = "distinct_but_overlapping"
    BROKERED = "brokered_shared_access"

    @property
    def code(self) -> str:
        return {Hypothesis.SAME: "H1", Hypothesis.OVERLAPPING: "H2", Hypothesis.BROKERED: "H3"}[self]


@dataclass(frozen=True)
class Revision:
    version: str
    date: str
    change: str


@dataclass
class Assessment:
    """A single adjudication, versioned and reviewable.

    The assessment holds the question, the designations under comparison, the body of
    evidence, the **source registry** (who said it and who repeats whom) and the graded
    judgement. ``declared`` records whether the dossier actually stated a confidence: a
    missing grade is not silently defaulted to ``low``, it is a finding (``no-grade``) and
    the tool refuses it.
    """

    id: str
    question: str
    subjects: list[Designation] = field(default_factory=list)
    hypotheses: list[Hypothesis] = field(default_factory=lambda: list(Hypothesis))
    evidence: list[Evidence] = field(default_factory=list)
    sources: list[dict[str, Any]] = field(default_factory=list)
    judgement: Judgement = field(default_factory=lambda: Judgement(Confidence.LOW))
    declared: bool = True
    requirement_id: str = ""
    review_trigger: str = ""
    review_by: str = ""
    gaps: list[str] = field(default_factory=list)
    revisions: list[Revision] = field(default_factory=list)
    version: str = "1.0"
    tlp: str = DEFAULT_TLP

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Assessment:
        subjects = [
            Designation(
                vendor=item["vendor"],
                name=item["name"],
                source_url=item.get("source_url", ""),
                date=item.get("date", ""),
                tlp=item.get("tlp", DEFAULT_TLP),
            )
            for item in data.get("subjects", [])
        ]
        evidence = [
            Evidence(
                id=item["id"],
                statement=item["statement"],
                source=item["source"],
                type=EvidenceType(item["type"]),
                consistency={
                    key: Consistency(value) for key, value in item.get("consistency", {}).items()
                },
                source_id=item.get("source_id", ""),
                reliability=item.get("reliability", ""),
            )
            for item in data.get("evidence", [])
        ]
        revisions = [
            Revision(version=item["version"], date=item["date"], change=item["change"])
            for item in data.get("revisions", [])
        ]
        judgement_data = data.get("judgement") or {}
        declared = bool(judgement_data.get("confidence"))
        judgement = Judgement(
            confidence=parse_confidence(judgement_data.get("confidence", Confidence.LOW.value)),
            probability=parse_probability(judgement_data.get("probability")),
        )
        return cls(
            id=data.get("id") or "",
            question=data.get("question") or "",
            subjects=subjects,
            hypotheses=[Hypothesis(value) for value in data.get("hypotheses", [h.value for h in Hypothesis])],
            evidence=evidence,
            sources=list(data.get("sources") or []),
            judgement=judgement,
            declared=declared,
            requirement_id=data.get("requirement_id", ""),
            review_trigger=data.get("review_trigger", ""),
            review_by=data.get("review_by", ""),
            gaps=list(data.get("gaps", [])),
            revisions=revisions,
            version=data.get("version", "1.0"),
            tlp=data.get("tlp", DEFAULT_TLP),
        )


def load_assessment(path: str | Path) -> Assessment:
    """Load an assessment from a JSON dossier."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return Assessment.from_dict(data)
