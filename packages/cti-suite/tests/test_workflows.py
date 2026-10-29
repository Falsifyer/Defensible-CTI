"""The supply chain of the workflows is part of the contract."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
WORKFLOWS = ROOT / ".github" / "workflows"


def test_every_action_is_pinned_to_a_commit() -> None:
    """A tag is mutable; a workflow that trusts one trusts whoever can move it."""
    for path in sorted(WORKFLOWS.glob("*.yml")):
        for line in path.read_text(encoding="utf-8").splitlines():
            match = re.search(r"\buses:\s*([^\s#]+)", line)
            if not match:
                continue
            reference = match.group(1)
            assert "@" in reference, f"{path.name}: {line.strip()}"
            sha = reference.rsplit("@", 1)[1]
            assert re.fullmatch(r"[0-9a-f]{40}", sha), f"{path.name}: {line.strip()}"
