"""Tests for the external-truth filter and the adjudicated corpus."""

from __future__ import annotations

from cryptonym.evaluate.adjudication import (
    Adjudication,
    Source,
    SourceCategory,
    SourceKind,
    Standard,
    Truth,
    filter_adjudication,
    independent_sources,
    validate_corpus,
)
from cryptonym.evaluate.metrics import evaluate_adjudicated


def _src(publisher, kind=SourceKind.ASSERTS_SAME, category=SourceCategory.VENDOR, derived=()):
    return Source(publisher=publisher, url="https://example.org/x", category=category, kind=kind, derived_from=derived)


def _adj(truth, standard, *sources):
    return Adjudication(truth=truth, standard=standard, sources=tuple(sources))


def _evidence(consistency=None):
    return [
        {
            "id": "E1",
            "statement": "shared tradecraft",
            "source": "s",
            "type": "tactics",
            "consistency": consistency or {"same_actor": "C"},
        }
    ]


def test_independence_drops_derived_and_same_publisher() -> None:
    sources = [
        _src("MITRE ATT&CK", category=SourceCategory.COMMUNITY),
        _src("Malpedia", derived=("MITRE ATT&CK",)),
        _src("MITRE ATT&CK", category=SourceCategory.COMMUNITY),  # same publisher
        _src("Microsoft"),
    ]
    independent = independent_sources(sources)
    assert [source.publisher for source in independent] == ["MITRE ATT&CK", "Microsoft"]


def test_author_assertion_and_single_source_are_never_external_truth() -> None:
    for standard in (Standard.AUTHOR_ASSERTION, Standard.SINGLE_SOURCE):
        verdict = filter_adjudication(_adj(Truth.SAME_ACTOR, standard, _src("A"), _src("B")))
        assert verdict.admissible is False
        assert verdict.effective_truth is Truth.UNADJUDICATED


def test_vendor_consensus_needs_two_independent_sources() -> None:
    insufficient = filter_adjudication(_adj(Truth.SAME_ACTOR, Standard.VENDOR_CONSENSUS, _src("A")))
    assert insufficient.admissible is False

    enough = filter_adjudication(_adj(Truth.SAME_ACTOR, Standard.VENDOR_CONSENSUS, _src("A"), _src("B")))
    assert enough.admissible is True
    assert enough.effective_truth is Truth.SAME_ACTOR


def test_government_statement_needs_corroboration() -> None:
    alone = filter_adjudication(
        _adj(Truth.SAME_ACTOR, Standard.GOVERNMENT_STATEMENT, _src("CISA", category=SourceCategory.GOVERNMENT))
    )
    assert alone.admissible is False

    corroborated = filter_adjudication(
        _adj(
            Truth.SAME_ACTOR,
            Standard.GOVERNMENT_STATEMENT,
            _src("CISA", category=SourceCategory.GOVERNMENT),
            _src("Microsoft"),
        )
    )
    assert corroborated.admissible is True


def test_hard_conflict_is_contested() -> None:
    verdict = filter_adjudication(
        _adj(
            Truth.SAME_ACTOR,
            Standard.INDEPENDENT_CORROBORATION,
            _src("A", kind=SourceKind.ASSERTS_SAME),
            _src("B", kind=SourceKind.ASSERTS_DISTINCT),
        )
    )
    assert verdict.effective_truth is Truth.CONTESTED
    assert verdict.admissible is False


def test_scope_dissent_downgrades_an_uncorroborated_claim() -> None:
    verdict = filter_adjudication(
        _adj(
            Truth.SAME_ACTOR,
            Standard.GOVERNMENT_STATEMENT,
            _src("CISA", category=SourceCategory.GOVERNMENT),
            _src("Dragos", kind=SourceKind.OVERLAP),
        )
    )
    assert verdict.effective_truth is Truth.CONTESTED


def test_scope_dissent_with_two_corroborators_is_admissible() -> None:
    verdict = filter_adjudication(
        _adj(
            Truth.SAME_ACTOR,
            Standard.GOVERNMENT_STATEMENT,
            _src("CISA", category=SourceCategory.GOVERNMENT),
            _src("Microsoft"),
            _src("Dragos", kind=SourceKind.OVERLAP),
        )
    )
    assert verdict.admissible is True
    assert any("scope dissent" in reason for reason in verdict.reasons)


def test_declaring_same_when_sources_say_distinct_is_unadjudicated() -> None:
    verdict = filter_adjudication(
        _adj(Truth.SAME_ACTOR, Standard.INDEPENDENT_CORROBORATION, _src("A", kind=SourceKind.ASSERTS_DISTINCT))
    )
    assert verdict.effective_truth is Truth.UNADJUDICATED


def test_a_declared_contested_truth_is_never_binary() -> None:
    verdict = filter_adjudication(_adj(Truth.CONTESTED, None, _src("A"), _src("B")))
    assert verdict.admissible is False
    assert verdict.effective_truth is Truth.CONTESTED


def test_validate_corpus_flags_the_problems_it_should() -> None:
    document = {
        "cases": [
            {"id": "a", "question": "?", "evidence": [], "adjudication": {"truth": "same_actor"}},
            {"id": "a", "question": "?", "evidence": [], "adjudication": {"truth": "contested"}},
            {"id": "b", "evidence": [], "adjudication": {"truth": "same_actor", "standard": "vendor-consensus"}},
            {
                "id": "c",
                "question": "?",
                "evidence": [],
                "adjudication": {
                    "truth": "same_actor",
                    "standard": "vendor-consensus",
                    "sources": [
                        {"publisher": "x", "url": "ftp://x", "category": "vendor", "kind": "asserts-same"}
                    ],
                },
            },
        ]
    }
    problems = " | ".join(validate_corpus(document))
    assert "duplicate id" in problems
    assert "binary truth requires a standard" in problems
    assert "missing question" in problems
    assert "non-URL url" in problems


def test_evaluate_adjudicated_counts_only_admissible_cases() -> None:
    admissible = {
        "id": "same",
        "question": "?",
        "evidence": _evidence(),
        "judgement": {"confidence": "high"},
        "adjudication": {
            "truth": "same_actor",
            "standard": "vendor-consensus",
            "sources": [
                {"publisher": "A", "url": "https://a", "category": "vendor", "kind": "asserts-same"},
                {"publisher": "B", "url": "https://b", "category": "vendor", "kind": "asserts-same"},
            ],
        },
    }
    contested = {
        "id": "contested",
        "question": "?",
        "evidence": _evidence(),
        "judgement": {"confidence": "low"},
        "adjudication": {"truth": "contested"},
    }
    summary = evaluate_adjudicated({"cases": [admissible, contested]})
    assert summary["coverage"] == {"admissible": 1, "contested": 1, "unadjudicated": 0}
    assert summary["metrics"]["total"] == 1
