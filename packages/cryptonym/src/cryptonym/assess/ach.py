"""ACH over the actor taxonomy, on top of :mod:`cti_method.ach`.

The engine itself is generic (any hypothesis labels). This module keeps Cryptonym's
default: when no hypotheses are given, the three actor hypotheses are used. Everything
else is the shared implementation.
"""

from __future__ import annotations

from collections.abc import Sequence

from cti_method.ach import (
    consistency_matrix as _consistency_matrix,
)
from cti_method.ach import (
    consistent_with_everything,
    discriminating_evidence,
    identity_supporting_evidence,
)
from cti_method.ach import (
    inconsistency_counts as _inconsistency_counts,
)
from cti_method.ach import (
    least_inconsistent as _least_inconsistent,
)
from cti_method.ach import (
    tied_at_top as _tied_at_top,
)
from cti_method.evidence import Consistency, Evidence

from cryptonym.model.assessment import Hypothesis


def _labels(hypotheses: Sequence[Hypothesis | str] | None) -> list[str]:
    chosen = list(Hypothesis) if hypotheses is None else list(hypotheses)
    return [getattr(item, "value", None) or str(item) for item in chosen]


def consistency_matrix(
    evidence: list[Evidence], hypotheses: Sequence[Hypothesis | str] | None = None
) -> dict[str, dict[str, Consistency]]:
    return _consistency_matrix(evidence, _labels(hypotheses))


def inconsistency_counts(
    evidence: list[Evidence],
    hypotheses: Sequence[Hypothesis | str] | None = None,
    sources: Sequence[object] | None = None,
) -> dict[str, int]:
    return _inconsistency_counts(evidence, _labels(hypotheses), sources)


def least_inconsistent(
    evidence: list[Evidence],
    hypotheses: Sequence[Hypothesis | str] | None = None,
    sources: Sequence[object] | None = None,
) -> list[str]:
    return _least_inconsistent(evidence, _labels(hypotheses), sources)


def tied_at_top(
    evidence: list[Evidence],
    hypotheses: Sequence[Hypothesis | str] | None = None,
    sources: Sequence[object] | None = None,
) -> list[str]:
    return _tied_at_top(evidence, _labels(hypotheses), sources)


__all__ = [
    "consistency_matrix",
    "consistent_with_everything",
    "discriminating_evidence",
    "identity_supporting_evidence",
    "inconsistency_counts",
    "least_inconsistent",
    "tied_at_top",
]
