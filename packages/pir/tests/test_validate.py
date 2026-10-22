import datetime as dt
import json

from pir_ledger.cli import main
from pir_ledger.validate import validate

TODAY = dt.date(2026, 10, 22)


def document(**changes):
    pir = {
        "id": "PIR-001",
        "question": "Which actors attack the supply chain of the energy sector?",
        "decision": "Which suppliers enter the quarterly monitoring plan.",
        "consumer": "Intelligence team",
        "priority": "high",
        "deadline": "2026-12-31",
        "status": "open",
        "eei": [
            {
                "id": "EEI-001",
                "question": "Are there documented campaigns against sector suppliers?",
                "indicators": [{"value": "campaigns published this quarter", "source": "B2"}],
            }
        ],
    }
    pir.update(changes)
    return {"version": "1.0", "requirements": [pir]}


def codes(doc):
    return {h["code"] for h in validate(doc, TODAY)["findings"]}


def test_a_correct_register_has_no_findings():
    r = validate(document(), TODAY)
    assert r["valid"] is True
    assert r["findings"] == []
    assert r["high"] == 0


def test_a_pir_without_a_decision_is_not_a_pir():
    doc = document(decision="")
    assert validate(doc, TODAY)["valid"] is False
    assert "no-decision" in codes(doc)


def test_no_consumer_fails():
    assert "no-consumer" in codes(document(consumer="  "))


def test_a_statement_without_a_question_mark_warns():
    doc = document(question="Monitor the energy sector")
    assert validate(doc, TODAY)["valid"] is True  # es media, no alta
    assert "not-a-question" in codes(doc)


def test_an_ungraded_indicator_invalidates_the_register():
    doc = document()
    doc["requirements"][0]["eei"][0]["indicators"] = [{"value": "algo"}]
    assert validate(doc, TODAY)["valid"] is False
    assert "indicator-ungraded" in codes(doc)


def test_a_grade_outside_the_scale_warns():
    doc = document()
    doc["requirements"][0]["eei"][0]["indicators"] = [{"value": "algo", "source": "Z9"}]
    assert "bad-admiralty" in codes(doc)


def test_no_eei_means_there_is_nothing_to_collect():
    assert "no-eei" in codes(document(eei=[]))


def test_overdue_and_unanswered_warns():
    assert "stale" in codes(document(deadline="2026-01-01"))


def test_identificadores_repetidos():
    doc = document()
    doc["requirements"].append(document()["requirements"][0])
    assert "duplicate-id" in codes(doc)


def test_cli_exits_one_when_invalid(tmp_path, capsys):
    ruta = tmp_path / "pir.json"
    ruta.write_text(json.dumps(document(decision="")), encoding="utf-8")
    assert main(["validate", str(ruta), "--today", "2026-10-22"]) == 1
    assert "no-decision" in capsys.readouterr().out


def test_cli_exits_zero_and_lists(tmp_path, capsys):
    ruta = tmp_path / "pir.json"
    ruta.write_text(json.dumps(document()), encoding="utf-8")
    assert main(["validate", str(ruta), "--today", "2026-10-22", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["valid"] is True
    assert main(["list", str(ruta), "--today", "2026-10-22"]) == 0
    assert "PIR-001" in capsys.readouterr().out


def test_findings_are_in_english_like_the_rest_of_the_suite() -> None:
    result = validate({"requirements": [{"id": "PIR-1", "question": "?", "priority": "high", "eei": []}]})
    messages = {item["code"]: item["message"] for item in result["findings"]}
    assert messages["no-decision"] == (
        "does not name the decision it informs: that is a topic of interest, not a PIR"
    )
    assert messages["no-consumer"] == "does not say who takes that decision"
    assert messages["no-eei"] == "no EEI: there is nothing to collect"
    # Guard against Spanish leaking back into the user-facing messages.
    SPANISH = ("no hay", "sin ", "el registro", "la pregunta")
    for message in messages.values():
        assert not any(word in message for word in SPANISH)
