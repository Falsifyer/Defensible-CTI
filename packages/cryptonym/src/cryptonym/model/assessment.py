"""An assessment: the graded, versioned judgement linking two designations."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from cryptonym.model.confidence import Confidence, Judgement, parse_confidence, parse_probability
from cryptonym.model.designation import Designation
from cryptonym.model.evidence import Consistency, Evidence, EvidenceType


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
    evidence and the graded judgement. It carries a *review trigger* and a revision
    history so a correction is published as a new version, never as a silent edit.
    """

    id: str
    question: str
    subjects: list[Designation] = field(default_factory=list)
    hypotheses: list[Hypothesis] = field(default_factory=lambda: list(Hypothesis))
    evidence: list[Evidence] = field(default_factory=list)
    judgement: Judgement = field(default_factory=lambda: Judgement(Confidence.LOW))
    review_trigger: str = ""
    gaps: list[str] = field(default_factory=list)
    revisions: list[Revision] = field(default_factory=list)
    version: str = "1.0"
    tlp: str = "TLP:WHITE"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Assessment:
        subjects = [
            Designation(
                vendor=item["vendor"],
                name=item["name"],
                source_url=item.get("source_url", ""),
                date=item.get("date", ""),
                tlp=item.get("tlp", "TLP:WHITE"),
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
            )
            for item in data.get("evidence", [])
        ]
        revisions = [
            Revision(version=item["version"], date=item["date"], change=item["change"])
            for item in data.get("revisions", [])
        ]
        judgement_data = data.get("judgement", {})
        judgement = Judgement(
            confidence=parse_confidence(judgement_data.get("confidence", "low")),
            probability=parse_probability(judgement_data.get("probability")),
        )
        return cls(
            id=data["id"],
            question=data["question"],
            subjects=subjects,
            hypotheses=[Hypothesis(value) for value in data.get("hypotheses", [h.value for h in Hypothesis])],
            evidence=evidence,
            judgement=judgement,
            review_trigger=data.get("review_trigger", ""),
            gaps=list(data.get("gaps", [])),
            revisions=revisions,
            version=data.get("version", "1.0"),
            tlp=data.get("tlp", "TLP:WHITE"),
        )


def load_assessment(path: str | Path) -> Assessment:
    """Load an assessment from a JSON dossier."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return Assessment.from_dict(data)
