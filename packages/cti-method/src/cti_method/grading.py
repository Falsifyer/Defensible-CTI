"""The grade a body of evidence can actually support.

The rule this module exists for: **a declared confidence is a claim about the evidence,
and the evidence sets a ceiling on it.** Without that, "two-axis confidence" is a text
field an analyst fills in, and the evaluation harness ends up calibrating prose.

The ceiling is deliberately conservative and stated in one place:

* **low** — no diagnostic item discriminates between the hypotheses. Shared tradecraft,
  vendor wording and structural overlap cannot carry a grade above low, however many
  items there are.
* **moderate** — at least one diagnostic item discriminates, but all of it comes from a
  single source.
* **high** — at least one diagnostic item discriminates **and** at least two independent
  sources contribute diagnostic evidence.

Independence is by ``source`` string, normalised: two citations of one publisher are one
voice. That is a coarse proxy — a dossier that needs finer independence should model its
sources as sources, not as strings — but it is checkable, and it fails closed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from cti_method.confidence import Confidence, parse_confidence
from cti_method.evidence import Evidence

_RANK = {Confidence.LOW: 1, Confidence.MODERATE: 2, Confidence.HIGH: 3}


@dataclass(frozen=True)
class EvidenceProfile:
    """What the evidence is made of, in the terms the ceiling is computed from."""

    evidence: int
    diagnostic_discriminating: tuple[str, ...]
    non_diagnostic: tuple[str, ...]
    consistent_with_everything: tuple[str, ...]
    independent_sources: int
    sources: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "evidence": self.evidence,
            "diagnostic_discriminating": list(self.diagnostic_discriminating),
            "non_diagnostic": list(self.non_diagnostic),
            "consistent_with_everything": list(self.consistent_with_everything),
            "independent_sources": self.independent_sources,
            "sources": list(self.sources),
        }


def _source_key(source: str) -> str:
    return " ".join((source or "").lower().split())


def profile(evidence: list[Evidence]) -> EvidenceProfile:
    """Describe the evidence by diagnostic strength and source independence."""
    diagnostic = [item for item in evidence if item.diagnostic and item.is_discriminating()]
    non_diagnostic = [item for item in evidence if not item.diagnostic]
    sources: list[str] = []
    for item in diagnostic:
        key = _source_key(item.source)
        if key and key not in sources:
            sources.append(key)
    return EvidenceProfile(
        evidence=len(evidence),
        diagnostic_discriminating=tuple(item.id for item in diagnostic),
        non_diagnostic=tuple(item.id for item in non_diagnostic),
        consistent_with_everything=tuple(item.id for item in evidence if not item.is_discriminating()),
        independent_sources=len(sources),
        sources=tuple(sources),
    )


def ceiling(evidence: list[Evidence]) -> Confidence:
    """The strongest confidence this evidence can support."""
    described = profile(evidence)
    if not described.diagnostic_discriminating:
        return Confidence.LOW
    if described.independent_sources >= 2:
        return Confidence.HIGH
    return Confidence.MODERATE


def derived_grade(evidence: list[Evidence]) -> dict[str, Any]:
    """The ceiling, the profile and the reasons, as a machine-readable block."""
    described = profile(evidence)
    top = ceiling(evidence)
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
        if described.independent_sources >= 2:
            reasons.append(f"{described.independent_sources} independent sources contribute diagnostic evidence")
        else:
            reasons.append("diagnostic evidence comes from a single source: moderate is the ceiling")
    return {"ceiling": top.value, "profile": described.as_dict(), "reasons": reasons}


def check_declared(declared: Confidence | str | None, evidence: list[Evidence]) -> list[dict[str, str]]:
    """Findings for a declared grade that the evidence does not support.

    A declared grade *below* the ceiling is allowed: an analyst may be more cautious than
    the evidence. A declared grade *above* it is a high finding, and the tool refuses.
    """
    from cti_method.contract import HIGH, finding

    findings: list[dict[str, str]] = []
    top = ceiling(evidence)
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
