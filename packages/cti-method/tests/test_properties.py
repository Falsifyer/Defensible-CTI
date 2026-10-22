"""Properties the ceiling must have, checked over generated evidence.

Example-based tests check the cases someone thought of. These check the rule: a ceiling
is a cap, so adding non-diagnostic evidence cannot raise it and adding a duplicate of
something already present cannot raise it either.
"""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from cti_method.evidence import Consistency, Evidence, EvidenceType
from cti_method.grading import ceiling

DIAGNOSTIC = ("infrastructure", "code", "operator")
NON_DIAGNOSTIC = ("tactics", "linguistic", "structural", "open_source")

evidence_strategy = st.builds(
    Evidence,
    id=st.text(min_size=1, max_size=6),
    statement=st.just("s"),
    source=st.sampled_from(["A", "B", "C"]),
    type=st.sampled_from([EvidenceType(value) for value in DIAGNOSTIC + NON_DIAGNOSTIC]),
    consistency=st.fixed_dictionaries(
        {},
        optional={
            "x": st.sampled_from(list(Consistency)),
            "y": st.sampled_from(list(Consistency)),
        },
    ),
)


@given(st.lists(evidence_strategy, max_size=8))
def test_the_ceiling_is_always_one_of_the_three_bands(evidence: list[Evidence]) -> None:
    assert ceiling(evidence).value in {"low", "moderate", "high"}


@given(st.lists(evidence_strategy, max_size=8))
def test_adding_shared_tradecraft_never_raises_the_ceiling(evidence: list[Evidence]) -> None:
    before = ceiling(evidence)
    added = evidence + [
        Evidence(
            id="extra-tactics",
            statement="s",
            source="Z",
            type=EvidenceType.TACTICS,
            consistency={"x": Consistency.CONSISTENT, "y": Consistency.CONSISTENT},
        )
    ]
    order = {"low": 1, "moderate": 2, "high": 3}
    assert order[ceiling(added).value] <= order[before.value]


@given(st.lists(evidence_strategy, min_size=1, max_size=8))
def test_duplicating_an_item_from_the_same_source_never_raises_the_ceiling(
    evidence: list[Evidence],
) -> None:
    order = {"low": 1, "moderate": 2, "high": 3}
    duplicated = evidence + [
        Evidence(
            id=item.id + "-copy",
            statement=item.statement,
            source=item.source,
            type=item.type,
            consistency=item.consistency,
            source_id=item.source_id,
            reliability=item.reliability,
        )
        for item in evidence[:1]
    ]
    assert order[ceiling(duplicated).value] <= order[ceiling(evidence).value]


@given(st.lists(evidence_strategy, max_size=8))
def test_a_ceiling_never_changes_when_a_source_registry_is_added_without_derivation(
    evidence: list[Evidence],
) -> None:
    sources = [{"id": f"src{i}", "publisher": f"Publisher {i}"} for i in range(1, 4)]
    # Sin source_id no hay registro que consultar: el resultado no depende del registro.
    assert ceiling(evidence, sources) == ceiling(evidence)
