"""Generate the curated ATT&CK map shipped with HuntPlan.

ATT&CK v18 (October 2025) **deprecated Data Sources**: technique detections now live in
*Detection Strategies* and *Analytics*, which reference *Data Components*. This script
reads the official STIX collection and writes the curated subset HuntPlan ships, with the
provenance needed to reproduce it (collection version, modified date and SHA-256 of the
exact bytes).

    python packages/huntplan/scripts/build_attack_map.py            # download and rebuild
    python packages/huntplan/scripts/build_attack_map.py --stix f.json
    python packages/huntplan/scripts/build_attack_map.py --check    # fail if out of date

The output is committed, so the tools never need the network.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path
from typing import Any

SOURCE = (
    "https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/"
    "enterprise-attack/enterprise-attack.json"
)

#: The curated subset: techniques this tool ships detection strategies for. Small on
#: purpose — anything else is reported as unknown instead of guessed at.
TECHNIQUES = (
    "T1059",
    "T1003",
    "T1055",
    "T1071",
    "T1105",
    "T1547",
    "T1053",
    "T1112",
    "T1021",
    "T1078",
    "T1566",
    "T1047",
)

OUTPUT = Path(__file__).resolve().parents[1] / "src" / "huntplan" / "attack.json"


def _external_id(obj: dict[str, Any]) -> str | None:
    for reference in obj.get("external_references") or []:
        if reference.get("source_name") == "mitre-attack" and reference.get("external_id"):
            return str(reference["external_id"])
    return None


def _url(obj: dict[str, Any]) -> str | None:
    for reference in obj.get("external_references") or []:
        if reference.get("source_name") == "mitre-attack" and reference.get("url"):
            return str(reference["url"])
    return None


def build_map(bundle: dict[str, Any]) -> dict[str, Any]:
    objects = bundle["objects"]
    by_id = {obj["id"]: obj for obj in objects}
    collection = next(obj for obj in objects if obj["type"] == "x-mitre-collection")

    techniques: dict[str, dict[str, Any]] = {}
    for obj in objects:
        if obj["type"] != "attack-pattern" or obj.get("revoked") or obj.get("x_mitre_deprecated"):
            continue
        external = _external_id(obj)
        if external:
            techniques[external] = obj

    components = {obj["id"]: obj for obj in objects if obj["type"] == "x-mitre-data-component"}
    analytics = {obj["id"]: obj for obj in objects if obj["type"] == "x-mitre-analytic"}
    strategies = {obj["id"]: obj for obj in objects if obj["type"] == "x-mitre-detection-strategy"}

    # technique id -> detection strategies that detect it
    detected_by: dict[str, list[str]] = {}
    for rel in objects:
        if rel["type"] != "relationship" or rel.get("relationship_type") != "detects":
            continue
        source = strategies.get(rel["source_ref"])
        target = techniques.get(_external_id(by_id.get(rel["target_ref"], {})) or "")
        if source is None or target is None:
            continue
        external = _external_id(target)
        if external:
            detected_by.setdefault(external, []).append(source["id"])

    def strategy_record(strategy: dict[str, Any]) -> dict[str, Any]:
        analytic_records = []
        for analytic_id in strategy.get("x_mitre_analytic_refs") or []:
            analytic = analytics.get(analytic_id)
            if not analytic:
                continue
            log_sources = []
            for reference in analytic.get("x_mitre_log_source_references") or []:
                component = components.get(reference.get("x_mitre_data_component_ref", ""), {})
                log_sources.append(
                    {
                        "data_component": component.get("name", "unknown"),
                        "data_component_id": _external_id(component),
                        "channel": reference.get("channel") or reference.get("name") or "",
                    }
                )
            analytic_records.append(
                {
                    "id": _external_id(analytic),
                    "platforms": analytic.get("x_mitre_platforms") or [],
                    "log_sources": log_sources[:4],
                }
            )
        return {
            "id": _external_id(strategy),
            "name": strategy.get("name", ""),
            "url": _url(strategy),
            "analytics": analytic_records,
        }

    curated: dict[str, Any] = {}
    for technique_id in TECHNIQUES:
        technique = techniques.get(technique_id)
        if technique is None:
            raise SystemExit(f"{technique_id} is not in the collection; the curated list is stale")
        family = [technique_id] + [
            _external_id(obj) or ""
            for obj in objects
            if obj["type"] == "attack-pattern"
            and _external_id(obj)
            and _external_id(obj).startswith(f"{technique_id}.")
            and not obj.get("revoked")
        ]
        seen: set[str] = set()
        records = []
        for member in [technique_id, *family[1:]]:
            for strategy_id in detected_by.get(member, []):
                if strategy_id in seen:
                    continue
                seen.add(strategy_id)
                record = strategy_record(strategies[strategy_id])
                record["detects"] = member
                records.append(record)
        curated[technique_id] = {
            "name": technique.get("name", ""),
            "url": _url(technique),
            "subtechniques": sorted(item for item in family[1:]),
            "detection_strategies": records,
        }

    return {
        "source": SOURCE,
        "collection": collection.get("name"),
        "attack_version": collection.get("x_mitre_version"),
        "attack_spec_version": collection.get("x_mitre_attack_spec_version") or "3.3.0",
        "collection_modified": collection.get("modified"),
        "sha256": hashlib.sha256(json.dumps(bundle, sort_keys=True).encode()).hexdigest(),
        "generated_by": "packages/huntplan/scripts/build_attack_map.py",
        "note": (
            "ATT&CK v18 deprecated Data Sources. This map carries Detection Strategies and "
            "Analytics (with their Data Components), which replaced them."
        ),
        "techniques": dict(sorted(curated.items())),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stix", help="Local ATT&CK enterprise STIX file (default: download).")
    parser.add_argument("--check", action="store_true", help="Do not write; fail if the file is out of date.")
    args = parser.parse_args(argv)

    if args.stix:
        raw = Path(args.stix).read_bytes()
    else:
        with urllib.request.urlopen(SOURCE, timeout=180) as response:  # noqa: S310 - fixed URL
            raw = response.read()
    bundle = json.loads(raw)
    generated = build_map(bundle)
    generated["source_sha256"] = hashlib.sha256(raw).hexdigest()
    text = json.dumps(generated, indent=1, ensure_ascii=False, sort_keys=False) + "\n"

    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != text:
            print(f"{OUTPUT} is out of date; rerun without --check", file=sys.stderr)
            return 1
        print(f"{OUTPUT} is current")
        return 0
    OUTPUT.write_text(text, encoding="utf-8")
    techniques = len(generated["techniques"])
    strategies = sum(len(item["detection_strategies"]) for item in generated["techniques"].values())
    print(f"{OUTPUT}: {techniques} techniques, {strategies} detection strategies, {len(text) // 1024} KiB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
