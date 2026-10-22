import datetime as dt
import json

from pir_ledger.cli import main
from pir_ledger.validate import validate

HOY = dt.date(2026, 10, 22)


def documento(**cambios):
    pir = {
        "id": "PIR-001",
        "question": "Que actores atacan la cadena de suministro del sector energetico?",
        "decision": "Que proveedores entran en el plan de vigilancia del trimestre.",
        "consumer": "Equipo de inteligencia",
        "priority": "high",
        "deadline": "2026-12-31",
        "status": "open",
        "eei": [
            {
                "id": "EEI-001",
                "question": "Hay campanas documentadas contra proveedores del sector?",
                "indicators": [{"value": "campanas publicadas en el trimestre", "source": "B2"}],
            }
        ],
    }
    pir.update(cambios)
    return {"version": "1.0", "requirements": [pir]}


def codigos(doc):
    return {h["code"] for h in validate(doc, HOY)["findings"]}


def test_un_registro_correcto_no_tiene_hallazgos():
    r = validate(documento(), HOY)
    assert r["valid"] is True
    assert r["findings"] == []
    assert r["high"] == 0


def test_una_pir_sin_decision_no_es_una_pir():
    doc = documento(decision="")
    assert validate(doc, HOY)["valid"] is False
    assert "no-decision" in codigos(doc)


def test_sin_consumidor_falla():
    assert "no-consumer" in codigos(documento(consumer="  "))


def test_un_enunciado_sin_interrogacion_avisa():
    doc = documento(question="Vigilar el sector energetico")
    assert validate(doc, HOY)["valid"] is True  # es media, no alta
    assert "not-a-question" in codigos(doc)


def test_un_indicador_sin_graduar_invalida_el_registro():
    doc = documento()
    doc["requirements"][0]["eei"][0]["indicators"] = [{"value": "algo"}]
    assert validate(doc, HOY)["valid"] is False
    assert "indicator-ungraded" in codigos(doc)


def test_graduacion_fuera_de_escala_avisa():
    doc = documento()
    doc["requirements"][0]["eei"][0]["indicators"] = [{"value": "algo", "source": "Z9"}]
    assert "bad-admiralty" in codigos(doc)


def test_sin_eei_no_hay_nada_que_recolectar():
    assert "no-eei" in codigos(documento(eei=[]))


def test_vencida_sin_responder_avisa():
    assert "stale" in codigos(documento(deadline="2026-01-01"))


def test_identificadores_repetidos():
    doc = documento()
    doc["requirements"].append(documento()["requirements"][0])
    assert "duplicate-id" in codigos(doc)


def test_cli_sale_con_uno_si_invalido(tmp_path, capsys):
    ruta = tmp_path / "pir.json"
    ruta.write_text(json.dumps(documento(decision="")), encoding="utf-8")
    assert main(["validate", str(ruta), "--today", "2026-10-22"]) == 1
    assert "no-decision" in capsys.readouterr().out


def test_cli_sale_con_cero_y_lista(tmp_path, capsys):
    ruta = tmp_path / "pir.json"
    ruta.write_text(json.dumps(documento()), encoding="utf-8")
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
    for message in messages.values():
        assert "no hay" not in message and "sin " not in message
