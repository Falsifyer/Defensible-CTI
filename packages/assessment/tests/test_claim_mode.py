"""A factual claim has one hypothesis: the claim itself.

The ACH engine exists to compare alternatives. Not every product is an ACH: "MITRE records
C0029 as a campaign" has no competing hypothesis, and grading it by whether it distinguishes
actors caps it at ``low`` for the wrong reason. The claim mode grades it by whether the
evidence bears on it directly.
"""

from __future__ import annotations

from assessment.core import assess, ceiling_for

SOURCES = [
    {"id": "S1", "publisher": "CISA"},
    {"id": "S2", "publisher": "DOJ"},
]


def _document(*, direct: bool, sources: list[dict], grade: str = "high") -> dict:
    return {
        "id": "claim-1",
        "question": "Does MITRE record C0029 as a campaign?",
        "mode": "claim",
        "claim_type": "documentary",
        "why_no_alternatives": "a documentary fact, not a dispute between actors",
        "hypotheses": ["C0029 is a campaign"],
        "evidence": [
            {
                "id": f"E{index}",
                "statement": "documentary evidence",
                "source": source["publisher"].lower(),
                "source_id": source["id"],
                "type": "open_source",
                "direct": direct,
            }
            for index, source in enumerate(sources, start=1)
        ],
        "sources": sources,
        "judgement": {"confidence": grade},
    }


def test_a_claim_with_two_independent_direct_sources_supports_high() -> None:
    verdict = assess(_document(direct=True, sources=SOURCES))
    assert verdict["mode"] == "claim"
    assert verdict["ceiling"] == "high"
    assert verdict["grade_supported"] is True
    assert verdict["findings"] == []


def test_a_claim_with_one_source_is_capped_at_moderate() -> None:
    verdict = assess(_document(direct=True, sources=SOURCES[:1]))
    assert verdict["ceiling"] == "moderate"
    assert verdict["grade_supported"] is False
    assert any(item["code"] == "grade-exceeds-evidence" for item in verdict["findings"])


def test_contextual_evidence_caps_at_low() -> None:
    verdict = assess(_document(direct=False, sources=SOURCES, grade="low"))
    assert verdict["ceiling"] == "low"
    assert any("direct" in reason for reason in verdict["grade_reasons"])


def test_no_hypothesis_is_refused() -> None:
    document = _document(direct=True, sources=SOURCES, grade="low")
    document["hypotheses"] = []
    verdict = assess(document)
    assert any(item["code"] == "no-claim" and item["severity"] == "high" for item in verdict["findings"])


def test_ceiling_for_accepts_the_claim_mode() -> None:
    result = ceiling_for(_document(direct=True, sources=SOURCES)["evidence"], mode="claim")
    assert result["ceiling"] == "high"


def _codes(verdict: dict) -> set[str]:
    return {item["code"] for item in verdict["findings"]}


def test_a_one_hypothesis_claim_must_declare_its_mode() -> None:
    document = _document(direct=True, sources=SOURCES)
    document.pop("mode")
    assert "claim-mode-unstated" in _codes(assess(document))


def test_an_identity_question_cannot_use_claim_mode() -> None:
    document = _document(direct=True, sources=SOURCES)
    document["claim_type"] = "identity"
    assert "identity-in-claim-mode" in _codes(assess(document))


def test_direct_evidence_is_only_for_documentary_claims() -> None:
    document = _document(direct=True, sources=SOURCES)
    document["claim_type"] = "estimative"
    assert "direct-not-documentary" in _codes(assess(document))


def test_claim_mode_refuses_competing_hypotheses() -> None:
    document = _document(direct=True, sources=SOURCES)
    document["hypotheses"] = ["A", "B"]
    assert "claim-mode-alternatives" in _codes(assess(document))
