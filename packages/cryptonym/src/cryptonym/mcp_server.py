"""Cryptonym as a Model Context Protocol server.

Exposes the reconciliation method — assess, render, export, ingest, adjudicate,
reconcile, snapshot — as MCP tools, so an agent drives the same engine the CLI and the
library use. Standard input/output transport; no background service required.

Run it directly:

    cryptonym-mcp

or register it in an MCP client (see ``docs/mcp.md``).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mcp.server.mcpserver import MCPServer

from cryptonym import __version__
from cryptonym.assess.grading import assess_actor_pair
from cryptonym.config import EXPORT_FORMATS, SUPPORTED_SOURCES
from cryptonym.evaluate.adjudication import validate_corpus
from cryptonym.evaluate.metrics import evaluate_adjudicated
from cryptonym.export.markdown import render_assessment
from cryptonym.export.misp_galaxy import to_misp_galaxy_cluster
from cryptonym.export.stix_bundle import to_stix_bundle
from cryptonym.export.taxii import to_taxii_envelope
from cryptonym.ingest import from_document
from cryptonym.model.assessment import load_assessment
from cryptonym.model.confidence import parse_confidence
from cryptonym.reconcile.graph import Linkage, Reconciliation

server = MCPServer(
    name="cryptonym",
    title="Cryptonym",
    version=__version__,
    instructions=(
        "Actor alias reconciliation with provenance and graded confidence. "
        "A merge is a hypothesis, not a fact."
    ),
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DOCS = {"method", "adjudication", "architecture", "data-model", "evaluating-alias-reconciliation"}


def _error(prefix: str, exc: Exception) -> dict[str, str]:
    return {"error": f"{prefix}: {type(exc).__name__}: {exc}"}


@server.tool()
def assess_dossier(path: str) -> dict[str, Any]:
    """Re-derive the graded judgement for a saved assessment dossier.

    Returns the hypotheses ranked by least-inconsistent evidence, the inconsistencies per
    hypothesis, the evidence that discriminates, the evidence that can support identity,
    and the two-axis grade.
    """
    try:
        return assess_actor_pair(load_assessment(path))
    except (OSError, ValueError, KeyError) as exc:
        return _error("assess failed", exc)


@server.tool()
def render_dossier(path: str) -> str:
    """Render a saved assessment dossier as a reviewable markdown product."""
    try:
        return render_assessment(load_assessment(path))
    except (OSError, ValueError, KeyError) as exc:
        return f"render failed: {type(exc).__name__}: {exc}"


@server.tool()
def export_dossier(path: str, format: str = "stix") -> dict[str, Any]:
    """Export a dossier as STIX 2.1, MISP Galaxy or TAXII 2.1, preserving confidence."""
    if format not in EXPORT_FORMATS:
        return {"error": f"unknown format {format!r}; expected one of: {', '.join(EXPORT_FORMATS)}"}
    try:
        assessment = load_assessment(path)
        if format == "stix":
            return to_stix_bundle(assessment)
        if format == "misp":
            return to_misp_galaxy_cluster(assessment)
        return to_taxii_envelope(assessment)
    except (OSError, ValueError, KeyError) as exc:
        return _error("export failed", exc)


@server.tool()
def ingest_document(source: str, path: str) -> dict[str, Any]:
    """Map a saved source document into separate designations (never a flat alias list).

    source is one of: misp-galaxy, attack-stix, opencti.
    """
    if source not in SUPPORTED_SOURCES:
        return {"error": f"unknown source {source!r}; expected one of: {', '.join(SUPPORTED_SOURCES)}"}
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        designations = from_document(source, data)
        return {
            "count": len(designations),
            "designations": [
                {"vendor": item.vendor, "name": item.name, "source_url": item.source_url, "date": item.date}
                for item in designations
            ],
        }
    except (OSError, ValueError, KeyError) as exc:
        return _error("ingest failed", exc)


@server.tool()
def adjudicate_corpus(path: str, strict: bool = False) -> dict[str, Any]:
    """Run the external-truth filter over an adjudicated corpus.

    Returns metrics, calibration, coverage (admissible / contested / unadjudicated), the
    standards used and the per-case verdict. With strict=True it also reports any binary
    truth that was not earned from independent sources.
    """
    try:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
        problems = validate_corpus(document)
        if problems:
            return {"valid": False, "problems": problems}
        summary = evaluate_adjudicated(document)
        result: dict[str, Any] = {
            "valid": True,
            "metrics": summary["metrics"],
            "calibration": summary["calibration"],
            "coverage": summary["coverage"],
            "by_standard": summary["by_standard"],
            "results": summary["results"],
        }
        if strict:
            unearned = [
                row["id"]
                for row in summary["results"]
                if row["declared_truth"] in ("same_actor", "distinct") and not row["admissible"]
            ]
            result["unearned"] = unearned
            result["strict_ok"] = not unearned
        return result
    except (OSError, ValueError, KeyError) as exc:
        return _error("adjudicate failed", exc)


@server.tool()
def reconcile_linkages(linkages: list[dict], minimum: str = "moderate") -> dict[str, Any]:
    """Cluster designations from graded linkages at a confidence threshold.

    Each linkage is {"left", "right", "confidence", "assessment_id"}. Returns the clusters
    at or above `minimum` and each cluster's weakest link: confidence is never averaged
    along a chain of same-as assertions.
    """
    try:
        parsed = [
            Linkage(
                left=item["left"],
                right=item["right"],
                confidence=parse_confidence(item["confidence"]),
                assessment_id=item.get("assessment_id", ""),
            )
            for item in linkages
        ]
        reconciliation = Reconciliation(parsed)
        clusters = []
        for cluster in reconciliation.clusters(parse_confidence(minimum)):
            weakest = reconciliation.weakest_link(cluster)
            clusters.append(
                {
                    "members": sorted(cluster),
                    "weakest_link": weakest.confidence.value if weakest else None,
                }
            )
        return {"minimum": minimum, "clusters": clusters}
    except (KeyError, ValueError) as exc:
        return _error("reconcile failed", exc)


@server.tool()
def snapshot_verify(path: str) -> dict[str, Any]:
    """Re-check that a recorded source snapshot still matches its SHA-256."""
    from cryptonym.snapshot import load

    try:
        recorded = load(path)
        return {"source": recorded.source, "sha256": recorded.sha256, "verified": recorded.verify()}
    except (OSError, ValueError, KeyError) as exc:
        return _error("snapshot verify failed", exc)


@server.tool()
def snapshot_source(url: str, allow_private: bool = False) -> dict[str, Any]:
    """Fetch an HTTP(S) source and capture its bytes and SHA-256 (SSRF-validated).

    Uses the network. Returns the snapshot; write it to disk with the CLI if you want to
    keep it.
    """
    from cryptonym import snapshot

    try:
        captured = snapshot.fetch(url, allow_private=allow_private)
        return captured.to_dict()
    except (OSError, ValueError) as exc:
        return _error("snapshot fetch failed", exc)


@server.tool()
def documentation(section: str = "method") -> dict[str, Any]:
    """Return a Cryptonym method document (method, adjudication, architecture, data-model)."""
    if section not in _DOCS:
        return {"error": f"unknown section {section!r}; expected one of: {', '.join(sorted(_DOCS))}"}
    path = _REPO_ROOT / "docs" / f"{section}.md"
    if not path.exists():
        return {"error": "documentation not found; install Cryptonym from its repository (editable)"}
    return {"section": section, "content": path.read_text(encoding="utf-8")}


def main() -> None:
    """Entry point: run the MCP server over standard input/output."""
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
