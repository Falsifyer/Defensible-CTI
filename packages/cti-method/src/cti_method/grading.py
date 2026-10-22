"""The grade a body of evidence can actually support.

The rule this module exists for: **a declared confidence is a claim about the evidence,
and the evidence sets a ceiling on it.** Without that, "two-axis confidence" is a text
field an analyst fills in, and the evaluation harness ends up calibrating prose.

The ceiling is deliberately conservative and stated in one place:

* **low** — no diagnostic item discriminates between the hypotheses. Shared tradecraft,
  vendor wording and structural overlap cannot carry a grade above low, however many
  items there are.
* **moderate** — at least one diagnostic item discriminates, but all of it comes from a
  single independent source.
* **high** — at least one diagnostic item discriminates **and** at least two independent
  sources contribute diagnostic evidence.

Two things move it down:

* **independence is structural** — a source that derives from another present is not a
  second voice, and two reports from one publisher are one voice (``sources.py``);
* **contradiction is not density** — if the diagnostic evidence that contradicts the
  favoured hypothesis outweighs the diagnostic evidence that supports it, the ceiling
  drops one step. Three strong items pointing the other way do not raise a grade.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from cti_method.confidence import Confidence
from cti_method.evidence import DIAGNOSTIC_TYPES, Consistency, Evidence
from cti_method.sources import attribute, independent_ids, registry

_RANK = {Confidence.LOW: 1, Confidence.MODERATE: 2, Confidence.HIGH: 3}
_BY_RANK = {value: key for key, value in _RANK.items()}


@dataclass(frozen=True)
class EvidenceProfile:
    """What the evidence is made of, in the terms the ceiling is computed from."""

    evidence: int
    diagnostic_discriminating: tuple[str, ...]
    non_diagnostic: tuple[str, ...]
    consistent_with_everything: tuple[str, ...]
    independent_sources: int
    sources: tuple[str, ...]
    source_ids: tuple[str, ...]
    registered: bool
    inconsistent_weight: float
    consistent_weight: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "evidence": self.evidence,
            "diagnostic_discriminating": list(self.diagnostic_discriminating),
            "non_diagnostic": list(self.non_diagnostic),
            "consistent_with_everything": list(self.consistent_with_everything),
            "independent_sources": self.independent_sources,
            "sources": list(self.sources),
            "source_ids": list(self.source_ids),
            "registered_sources": self.registered,
            "inconsistent_weight": self.inconsistent_weight,
            "consistent_weight": self.consistent_weight,
        }


def profile(
    evidence: list[Evidence],
    sources: list[Any] | None = None,
    favoured: str | None = None,
) -> EvidenceProfile:
    """Describe the evidence by diagnostic strength, independence and direction."""
    known = registry(sources)
    diagnostic = [item for item in evidence if item.diagnostic and item.is_discriminating()]
    non_diagnostic = [item for item in evidence if not item.diagnostic]

    keys: list[str] = []
    ids: list[str] = []
    registered = False
    for item in diagnostic:
        key = attribute(item.source, item.source_id, known)
        registered = registered or key.registered
        if key.key and key.key not in keys:
            keys.append(key.key)
            ids.append(item.source_id or key.key)
    independent = independent_ids(keys, known) if registered else keys

    inconsistent = 0.0
    consistent = 0.0
    if favoured:
        for item in evidence:
            if item.type not in DIAGNOSTIC_TYPES:
                continue
            verdict = item.consistency.get(favoured, Consistency.NEUTRAL)
            if verdict is Consistency.INCONSISTENT:
                inconsistent += item.weight
            elif verdict is Consistency.CONSISTENT:
                consistent += item.weight

    return EvidenceProfile(
        evidence=len(evidence),
        diagnostic_discriminating=tuple(item.id for item in diagnostic),
        non_diagnostic=tuple(item.id for item in non_diagnostic),
        consistent_with_everything=tuple(item.id for item in evidence if not item.is_discriminating()),
        independent_sources=len(independent),
        sources=tuple(keys),
        source_ids=tuple(ids),
        registered=registered,
        inconsistent_weight=round(inconsistent, 4),
        consistent_weight=round(consistent, 4),
    )


def ceiling(
    evidence: list[Evidence],
    sources: list[Any] | None = None,
    favoured: str | None = None,
) -> Confidence:
    """The strongest confidence this evidence can support."""
    described = profile(evidence, sources, favoured)
    if not described.diagnostic_discriminating:
        return Confidence.LOW
    top = Confidence.HIGH if described.independent_sources >= 2 else Confidence.MODERATE
    if described.inconsistent_weight > described.consistent_weight:
        top = _BY_RANK[_RANK[top] - 1]
    return top


def derived_grade(
    evidence: list[Evidence],
    sources: list[Any] | None = None,
    favoured: str | None = None,
) -> dict[str, Any]:
    """The ceiling, the profile and the reasons, as a machine-readable block."""
    described = profile(evidence, sources, favoured)
    top = ceiling(evidence, sources, favoured)
    reasons: list[str] = []
    if not described.diagnostic_discriminating:
        reasons.append(
            "no diagnostic item discriminates between the hypotheses: shared tradecraft "
            "and non-diagnostic overlap cannot support more than low confidence"
        )
    else:
        reasons.append(
            f"{len(described.diagnostic_discriminating)} diagnostic item(s) discriminate "
            f"({', '.join(described.diagnostic_discriminating)})"
        )
        if described.registered:
            reasons.append(
                f"{described.independent_sources} independent registered source(s) contribute "
                "diagnostic evidence (derived sources count once)"
            )
        elif described.independent_sources >= 2:
            reasons.append(f"{described.independent_sources} distinct source strings contribute diagnostic evidence")
        else:
            reasons.append(
                "diagnostic evidence comes from a single source: moderate is the ceiling "
                "(register the dossier's sources to make independence checkable)"
            )
        if described.inconsistent_weight > described.consistent_weight:
            reasons.append(
                f"diagnostic evidence against the favoured hypothesis outweighs the evidence for it "
                f"({described.inconsistent_weight} vs {described.consistent_weight}): the ceiling drops a step"
            )
    return {
        "ceiling": top.value,
        "favoured": favoured,
        "profile": described.as_dict(),
        "reasons": reasons,
    }


def check_declared(
    declared: Confidence | str | None,
    evidence: list[Evidence],
    sources: list[Any] | None = None,
    favoured: str | None = None,
) -> list[dict[str, str]]:
    """Findings for a declared grade that the evidence does not support.

    A declared grade *below* the ceiling is allowed: an analyst may be more cautious than
    the evidence. A declared grade *above* it is a high finding, and the tool refuses.
    """
    from cti_method.confidence import parse_confidence
    from cti_method.contract import HIGH, finding

    findings: list[dict[str, str]] = []
    top = ceiling(evidence, sources, favoured)
    declared = parse_confidence(declared) if declared is not None else None
    if declared is None:
        findings.append(
            finding(
                "no-grade",
                HIGH,
                f"the claim declares no confidence; the evidence supports at most {top.value}",
            )
        )
        return findings
    if _RANK[declared] > _RANK[top]:
        findings.append(
            finding(
                "grade-exceeds-evidence",
                HIGH,
                f"declared confidence {declared.value} exceeds what the evidence supports "
                f"({top.value}): add diagnostic evidence or lower the grade",
            )
        )
    return findings
