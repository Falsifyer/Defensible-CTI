"""Tag → package mapping for the release workflow, as testable code.

The workflow used to carry this mapping inline in YAML, where nothing could test it. It
lives here so the mapping can be exercised without tagging a repository, and the workflow
only reads the result.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tomllib
from pathlib import Path

#: tag prefix -> (distribution name, directory under packages/)
TARGETS: dict[str, tuple[str, str]] = {
    "cti-method": ("cti-method", "cti-method"),
    "cryptonym": ("cryptonym", "cryptonym"),
    "assessment": ("assessment-mcp", "assessment"),
    "sharegate": ("sharegate", "sharegate"),
    "stixforge": ("stix-forge", "stixforge"),
    "pir": ("pir-ledger", "pir"),
    "huntplan": ("huntplan", "huntplan"),
    "cti-suite": ("cti-suite", "cti-suite"),
}


def parse(tag: str) -> dict[str, str]:
    """Split ``<prefix>-v<version>`` and resolve the package it names."""
    if "-v" not in tag:
        raise ValueError(f"tag {tag!r} is not <package>-v<version>")
    prefix, version = tag.rsplit("-v", 1)
    if prefix not in TARGETS:
        raise ValueError(f"unknown tag prefix {prefix!r}; expected one of: {', '.join(sorted(TARGETS))}")
    if not version or not version[0].isdigit():
        raise ValueError(f"tag {tag!r} has no version")
    package, directory = TARGETS[prefix]
    return {"tag": tag, "prefix": prefix, "package": package, "directory": directory, "version": version}


def by_package(package: str, root: Path | None = None) -> dict[str, str]:
    """Resolve a distribution name to its directory, version and (unknown) prefix."""
    for prefix, (name, directory) in TARGETS.items():
        if name == package:
            version = declared_version(directory, root)
            target = {
                "tag": f"{prefix}-v{version}",
                "prefix": prefix,
                "package": name,
                "directory": directory,
                "version": version,
            }
            return target
    known = ", ".join(sorted({name for name, _ in TARGETS.values()}))
    raise ValueError(f"no package named {package!r}; expected one of: {known}")


def declared_version(directory: str, root: Path | None = None) -> str:
    """The version the package's own ``pyproject.toml`` declares."""
    base = root or Path(__file__).resolve().parents[4]
    data = tomllib.loads((base / "packages" / directory / "pyproject.toml").read_text(encoding="utf-8"))
    return str(data["project"]["version"])


def check(tag: str, root: Path | None = None) -> dict[str, str]:
    """Resolve the tag and fail if the package does not declare that version."""
    target = parse(tag)
    declared = declared_version(target["directory"], root)
    if declared != target["version"]:
        raise ValueError(f"tag says {target['version']}, packages/{target['directory']} says {declared}")
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--tag")
    group.add_argument("--package", help="Distribution name, for a publish that is not a tag.")
    parser.add_argument("--check", action="store_true", help="Also verify the package version.")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--github-output", action="store_true", help="Write key=value lines to $GITHUB_OUTPUT.")
    args = parser.parse_args(argv)

    try:
        if args.package:
            target = by_package(args.package)
        else:
            target = check(args.tag) if args.check else parse(args.tag)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.github_output:
        path = os.environ.get("GITHUB_OUTPUT")
        if not path:
            print("error: GITHUB_OUTPUT is not set", file=sys.stderr)
            return 2
        with Path(path).open("a", encoding="utf-8") as handle:
            for key, value in target.items():
                handle.write(f"{key}={value}\n")
    elif args.as_json:
        print(json.dumps(target, indent=2))
    else:
        for key, value in target.items():
            print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
