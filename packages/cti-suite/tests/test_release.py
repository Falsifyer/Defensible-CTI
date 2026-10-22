"""The release mapping is code, so it is tested like code."""

from __future__ import annotations

from pathlib import Path

import pytest

from cti_suite.release import TARGETS, check, parse

ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize(
    "tag",
    ["cryptonym-v0.7.0", "stixforge-v0.2.0", "pir-v0.2.0", "assessment-v0.2.0", "cti-suite-v0.1.0"],
)
def test_every_tag_resolves_to_a_package(tag: str) -> None:
    target = parse(tag)
    assert target["directory"] in {directory for _, directory in TARGETS.values()}
    assert target["version"].startswith("0.")


def test_the_versions_in_the_repository_match_their_tags() -> None:
    for prefix, (package, directory) in TARGETS.items():
        version = _version(directory)
        target = check(f"{prefix}-v{version}", ROOT)
        assert target["package"] == package


def _version(directory: str) -> str:
    for line in (ROOT / "packages" / directory / "pyproject.toml").read_text(encoding="utf-8").splitlines():
        if line.startswith("version = "):
            return line.split('"')[1]
    raise AssertionError(directory)


def test_a_tag_with_the_wrong_version_is_refused() -> None:
    with pytest.raises(ValueError, match="tag says"):
        check("cryptonym-v9.9.9", ROOT)


def test_an_unknown_prefix_is_refused() -> None:
    with pytest.raises(ValueError, match="unknown tag prefix"):
        parse("nonsense-v1.0.0")


def test_a_tag_without_a_version_is_refused() -> None:
    with pytest.raises(ValueError):
        parse("cryptonym")
