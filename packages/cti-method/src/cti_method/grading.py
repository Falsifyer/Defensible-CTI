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
    mode: str = "ach"
    direct: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "evidence": self.evidence,
            "diagnostic_discriminating": list(self.diagnostic_discriminating),
            "direct": list(self.direct),
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
    mode: str = "ach",
) -> EvidenceProfile:
    """Describe the evidence by diagnostic strength, independence and direction.

    Two modes, one rule for independence:

    * ``ach`` — what distinguishes the competing hypotheses: items whose type can bear on
      identity and that are not consistent with every hypothesis;
    * ``claim`` — what bears on a claim that has no alternatives: items marked ``direct``,
      whatever their evidence type. A documentary fact is not graded by whether it
      distinguishes actors.
    """
    known = registry(sources)
    if mode == "claim":
        represented = [item for item in evidence if item.direct]
        non_diagnostic = [item for item in evidence if not item.direct]
    else:
        represented = [item for item in evidence if item.diagnostic and item.is_discriminating()]
        non_diagnostic = [item for item in evidence if not item.diagnostic]

    keys: list[str] = []
    ids: list[str] = []
    registered = False
    for item in represented:
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
            if item.type not in DIAGNOSTIC_TYPES or not item.is_discriminating():
                continue
            verdict = item.consistency.get(favoured, Consistency.NEUTRAL)
            if verdict is Consistency.INCONSISTENT:
                inconsistent += item.weight
            elif verdict is Consistency.CONSISTENT:
                consistent += item.weight

    return EvidenceProfile(
        evidence=len(evidence),
        diagnostic_discriminating=tuple(item.id for item in represented) if mode == "ach" else (),
        non_diagnostic=tuple(item.id for item in non_diagnostic),
        consistent_with_everything=tuple(item.id for item in evidence if not item.is_discriminating()),
        independent_sources=len(independent),
        sources=tuple(keys),
        source_ids=tuple(ids),
        registered=registered,
        inconsistent_weight=round(inconsistent, 4),
        consistent_weight=round(consistent, 4),
        mode=mode,
        direct=tuple(item.id for item in evidence if item.direct),
    )


def ceiling(
    evidence: list[Evidence],
    sources: list[Any] | None = None,
    favoured: str | None = None,
    mode: str = "ach",
) -> Confidence:
    """The strongest confidence this evidence can support.

    With competing hypotheses (``mode="ach"``) the ceiling depends on diagnostic items
    that discriminate and on independent sources. For a claim with no alternatives
    (``mode="claim"``) it depends on items that bear directly on the claim, with the same
    independence rule and no contradiction step.
    """
    described = profile(evidence, sources, favoured, mode)
    if mode == "claim":
        if not described.direct:
            return Confidence.LOW
        return Confidence.HIGH if described.independent_sources >= 2 else Confidence.MODERATE
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
    mode: str = "ach",
) -> dict[str, Any]:
    """The ceiling, the profile and the reasons, as a machine-readable block."""
    described = profile(evidence, sources, favoured, mode)
    top = ceiling(evidence, sources, favoured, mode)
    reasons: list[str] = []
    if mode == "claim":
        if not described.direct:
            reasons.append(
                "no item bears directly on the claim: contextual or inferential evidence "
                "cannot support more than low confidence"
            )
        else:
            reasons.append(
                f"{len(described.direct)} direct item(s) bear on the claim "
                f"({', '.join(described.direct)})"
            )
            if described.registered:
                reasons.append(
                    f"{described.independent_sources} independent registered source(s) carry "
                    "direct evidence (derived sources count once)"
                )
            elif described.independent_sources >= 2:
                reasons.append(
                    f"{described.independent_sources} distinct source strings carry direct evidence"
                )
            else:
                reasons.append(
                    "direct evidence comes from a single source: moderate is the ceiling "
                    "(register the claim's sources to make independence checkable)"
                )
    elif not described.diagnostic_discriminating:
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
        "mode": mode,
        "favoured": favoured,
        "profile": described.as_dict(),
        "reasons": reasons,
    }


def policy() -> dict[str, Any]:
    """The grading policy, as data: one function, two modes, one independence rule.

    Exported so a consumer can render the standard it is being held to, instead of
    restating it in prose and drifting from the code.
    """
    return {
        "independence": {
            "rule": (
                "a source that derives from another present is not a second voice; two "
                "sources from one publisher are one voice"
            ),
            "derived_from": True,
        },
        "modes": {
            "ach": {
                "requires": "at least two competing hypotheses",
                "counts": (
                    "items whose type is infrastructure, code or operator and which are not "
                    "consistent with every hypothesis"
                ),
                "ceilings": {
                    "none": "low",
                    "one_independent_source": "moderate",
                    "two_independent_sources": "high",
                },
                "modifier": (
                    "if diagnostic weight against the favoured hypothesis exceeds the weight "
                    "for it, the ceiling drops one step"
                ),
            },
            "claim": {
                "requires": "one hypothesis — the claim itself — and no alternatives",
                "counts": "items that bear directly on the claim, whatever their evidence type",
                "ceilings": {
                    "none": "low",
                    "one_independent_source": "moderate",
                    "two_independent_sources": "high",
                },
                "modifier": "none: there is no competing hypothesis to weigh against",
            },
        },
    }


def check_declared(
    declared: Confidence | str | None,
    evidence: list[Evidence],
    sources: list[Any] | None = None,
    favoured: str | None = None,
    mode: str = "ach",
) -> list[dict[str, str]]:
    """Findings for a declared grade that the evidence does not support.

    A declared grade *below* the ceiling is allowed: an analyst may be more cautious than
    the evidence. A declared grade *above* it is a high finding, and the tool refuses.
    """
    from cti_method.confidence import parse_confidence
    from cti_method.contract import HIGH, finding

    findings: list[dict[str, str]] = []
    top = ceiling(evidence, sources, favoured, mode)
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
        hint = "direct evidence" if mode == "claim" else "diagnostic evidence"
        findings.append(
            finding(
                "grade-exceeds-evidence",
                HIGH,
                f"declared confidence {declared.value} exceeds what the evidence supports "
                f"({top.value}): add {hint} or lower the grade",
            )
        )
    return findings
