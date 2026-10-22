"""The house contract, exercised through the six real entry points.

This is the test the suite did not have: before this, three of the six returned 1 on a
missing file, which the README defines as "a high finding". A missing file is not an
infraction committed by the file.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from assessment.cli import main as assessment_main
from cryptonym.cli import main as cryptonym_main
from huntplan.cli import main as huntplan_main
from pir_ledger.cli import main as pir_main
from sharegate.cli import main as sharegate_main
from stixforge.cli import main as stixforge_main

MISSING = "does-not-exist.json"


@pytest.mark.parametrize(
    "name,run",
    [
        ("pir validate", lambda path: pir_main(["validate", path])),
        ("cryptonym assess", lambda path: cryptonym_main(["assess", path])),
        ("assessment assess", lambda path: assessment_main(["assess", path])),
        ("huntplan validate", lambda path: huntplan_main(["validate", path])),
        ("stixforge validate", lambda path: stixforge_main(["validate", path])),
        ("sharegate check", lambda path: sharegate_main(["check", path])),
    ],
)
def test_an_unreadable_file_is_exit_two_not_a_finding(tmp_path: Path, name: str, run) -> None:
    assert run(str(tmp_path / MISSING)) == 2, f"{name} reported a missing file as something other than cannot-check"


def test_a_high_finding_is_exit_one(tmp_path: Path) -> None:
    register = tmp_path / "pir.json"
    register.write_text(
        json.dumps({"schema_version": "1.0", "id": "r", "requirements": [{"id": "PIR-1", "question": "?"}]}),
        encoding="utf-8",
    )
    assert pir_main(["validate", str(register)]) == 1

    hypothesis = tmp_path / "h.txt"
    hypothesis.write_text("look around", encoding="utf-8")
    assert huntplan_main(["validate", str(hypothesis)]) == 1

    product = tmp_path / "product.json"
    product.write_text(
        json.dumps(
            {
                "title": "t",
                "author": "a",
                "tlp": "amber",
                "observables": [{"type": "domain-name", "value": "x.test"}],
            }
        ),
        encoding="utf-8",
    )
    assert stixforge_main(["build", str(product)]) == 1

    text = tmp_path / "product.md"
    text.write_text("TLP:CLEAR and TLP:RED", encoding="utf-8")
    assert sharegate_main(["check", str(text)]) == 1
