"""The ceiling for a claim that has no competing hypotheses (``mode="claim"``).

The ACH mode grades evidence by whether it distinguishes between hypotheses. A factual
claim — "MITRE records C0029 as a campaign" — has no alternatives to distinguish: the
question is whether the evidence bears on the claim directly, and how many independent
voices carry it. Without this mode the core caps every factual claim at ``low``, which
contradicts what ``assessment`` says it grades.
"""

from __future__ import annotations

from cti_method.evidence import Evidence, EvidenceType
from cti_method.grading import ceiling, derived_grade


def _item(
    evidence_id: str,
    source_id: str,
    direct: bool,
    kind: EvidenceType = EvidenceType.OPEN_SOURCE,
) -> Evidence:
    return Evidence(
        id=evidence_id,
        statement="s",
        source=source_id.lower(),
        type=kind,
        source_id=source_id,
        direct=direct,
    )


SOURCES = [
    {"id": "S1", "publisher": "CISA"},
    {"id": "S2", "publisher": "DOJ"},
]


def test_a_documented_fact_with_one_source_caps_at_moderate() -> None:
    evidence = [_item("E1", "S1", direct=True)]
    assert ceiling(evidence, SOURCES, mode="claim") == "moderate"


def test_two_independent_direct_sources_reach_high() -> None:
    evidence = [_item("E1", "S1", direct=True), _item("E2", "S2", direct=True)]
    assert ceiling(evidence, SOURCES, mode="claim") == "high"
    assert derived_grade(evidence, SOURCES, mode="claim")["profile"]["independent_sources"] == 2


def test_a_derived_source_is_not_a_second_voice() -> None:
    sources = [
        {"id": "S1", "publisher": "CISA"},
        {"id": "S2", "publisher": "DOJ", "derived_from": ["S1"]},
    ]
    evidence = [_item("E1", "S1", direct=True), _item("E2", "S2", direct=True)]
    assert ceiling(evidence, sources, mode="claim") == "moderate"


def test_two_ids_from_one_publisher_are_one_voice() -> None:
    sources = [{"id": "S1", "publisher": "Dragos"}, {"id": "S2", "publisher": "Dragos"}]
    evidence = [_item("E1", "S1", direct=True), _item("E2", "S2", direct=True)]
    assert ceiling(evidence, sources, mode="claim") == "moderate"


def test_an_assessment_with_no_direct_evidence_caps_at_low() -> None:
    evidence = [_item("E1", "S1", direct=False, kind=EvidenceType.LINGUISTIC)]
    assert ceiling(evidence, SOURCES, mode="claim") == "low"
    assert "direct" in " ".join(derived_grade(evidence, SOURCES, mode="claim")["reasons"])


def test_claim_mode_does_not_consult_evidence_types() -> None:
    # A documentary claim can be evidenced by a linguistic artefact; the type that
    # matters for identity (infrastructure/code/operator) is the wrong axis here.
    evidence = [
        _item("E1", "S1", direct=True, kind=EvidenceType.LINGUISTIC),
        _item("E2", "S2", direct=True, kind=EvidenceType.STRUCTURAL),
    ]
    assert ceiling(evidence, SOURCES, mode="claim") == "high"


def test_ach_mode_is_unchanged() -> None:
    evidence = [_item("E1", "S1", direct=True, kind=EvidenceType.TACTICS)]
    assert ceiling(evidence, SOURCES) == "low"
