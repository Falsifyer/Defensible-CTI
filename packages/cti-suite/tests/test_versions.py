"""Version numbers mean something only if the package and its metadata agree."""

from __future__ import annotations

import importlib
from importlib import metadata
from pathlib import Path

import pytest

PACKAGES = [
    ("cti-method", "cti-method", "cti_method"),
    ("cryptonym", "cryptonym", "cryptonym"),
    ("assessment-mcp", "assessment", "assessment"),
    ("sharegate", "sharegate", "sharegate"),
    ("stix-forge", "stixforge", "stixforge"),
    ("pir-ledger", "pir", "pir_ledger"),
    ("huntplan", "huntplan", "huntplan"),
    ("cti-suite", "cti-suite", "cti_suite"),
]

ROOT = Path(__file__).resolve().parents[3]


def _metadata_version(directory: str) -> str:
    text = (ROOT / "packages" / directory / "pyproject.toml").read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.startswith("version = "):
            return line.split('"')[1]
    raise AssertionError(f"no version in {directory}")


@pytest.mark.parametrize("distribution,directory,module", PACKAGES)
def test_the_module_version_matches_the_packaged_version(distribution: str, directory: str, module: str) -> None:
    installed = importlib.import_module(module)
    assert installed.__version__ == metadata.version(distribution)
    assert installed.__version__ == _metadata_version(directory)


def test_the_root_is_a_workspace_without_a_version() -> None:
    """The suite has no single number that means anything; each package has its own."""
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "version = " not in text.split("[tool.uv.workspace]")[0]
