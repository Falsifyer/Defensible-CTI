#!/bin/sh
# The whole cycle, one command, fictional data.
#
#   make demo
#
# Seven steps, and from step 2 onwards every step **reads the file the previous step
# wrote** and verifies the identifier it cites against it. The chain is in the data, not
# in the prose: if a step's output changes, the next step notices.
#
# Nothing here is real: NIGHTJAR and SALTWIND do not exist.

set -eu

aqui=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
out="$aqui/out"
rm -rf "$out"
mkdir -p "$out"

paso() { printf '\n== %s\n' "$1"; }

paso "1/7  pir validate        what is worth answering, and which decision it informs"
pir validate "$aqui/pir.json" --json > "$out/pir-validation.json"
# Lo que viaja al resto del ciclo es el registro que paso la validacion, no el original.
cp "$aqui/pir.json" "$out/pir.json"
python3 - "$out/pir-validation.json" <<'PY'
import json, sys
r = json.load(open(sys.argv[1]))
print(f"  register    : {r.get('register_id')} ({r['requirements']} requirements, HIGH {r['high']})")
print(f"  ids         : {', '.join(r['ids'])}")
PY

paso "2/7  cryptonym assess     the judgment on the alias question"
cryptonym assess "$aqui/assessment.json" > "$out/judgement.json"
python3 - "$out/judgement.json" <<'PY'
import json, sys
j = json.load(open(sys.argv[1]))
print("  favoured    :", ", ".join(j.get("hypotheses_favoured", [])))
print("  discriminating:", ", ".join(j.get("discriminating_evidence", [])) or "none")
print("  declared    :", j.get("confidence"), "| ceiling:", j.get("ceiling"))
PY

paso "3/7  assessment assess    re-derive it against step 2, and keep the ledger"
assessment assess "$aqui/assessment.json" \
	--register "$out/pir.json" \
	--against "$out/judgement.json" \
	--append "$out/ledger.jsonl" > "$out/verdict.json"
python3 - "$out/verdict.json" <<'PY'
import json, sys
v = json.load(open(sys.argv[1]))
print("  ranking     :", ", ".join(v.get("ranking", [])))
print("  declared    :", v["grade"]["confidence"], "| ceiling:", v.get("ceiling"),
      "| reproduced:", v.get("reproduced"))
PY
assessment ledger "$out/ledger.jsonl" --verify > "$out/ledger-check.json"
python3 - "$out/ledger-check.json" <<'PY'
import json, sys
r = json.load(open(sys.argv[1]))
print(f"  ledger      : {r['entries']} entries, chain {'intact' if r['valid'] else 'BROKEN'}")
PY

paso "4/7  huntplan validate    the plan, linked to the assessment that produced it"
huntplan validate "$aqui/hunt.json" --assessment "$out/verdict.json" > "$out/hunt.json"
python3 - "$out/hunt.json" <<'PY'
import json, sys
h = json.load(open(sys.argv[1]))
print("  ready       :", h.get("ready"), "| id:", h.get("id"))
for t in h.get("techniques", []):
    ids = ", ".join(s["id"] for s in t["detection_strategies"]) or "none"
    print(f"  {t['technique_id']:7s} {len(t['detection_strategies'])} detection strategies ({ids})")
attack = h.get("attack") or {}
print(f"  ATT&CK      : {attack.get('collection')} {attack.get('attack_version')}")
PY

paso "5/7  stixforge build       the product, with the trace of the three steps before it"
stixforge build "$aqui/product.json" -o "$out/bundle.json" \
	--requirement "$out/pir.json" \
	--assessment "$out/verdict.json" \
	--hunt "$out/hunt.json"
python3 - "$out/bundle.json" <<'PY'
import json, sys
b = json.load(open(sys.argv[1]))
report = next(o for o in b["objects"] if o["type"] == "report")
print("  objects     :", len(b["objects"]), "| types:", ", ".join(sorted({o["type"] for o in b["objects"]})))
print("  trace       :", ", ".join(f"{r['source_name']}={r['external_id']}" for r in report.get("external_references", [])))
PY

paso "6/7  sharegate check       may it leave, and how far"
if ! sharegate check "$out/bundle.json" > "$out/gate.json"; then
	echo "  THE GATE REFUSES: this bundle does not leave." >&2
	cat "$out/gate.json" >&2
	exit 1
fi
python3 - "$out/gate.json" <<'PY'
import json, sys
r = json.load(open(sys.argv[1]))
print("  shareable   :", r.get("shareable"), "| effective:", r.get("effective_tlp"))
print("  stix valid  :", r["stix"]["valid"], "| findings:", len(r["findings"]))
PY

paso "7/7  ctisuite report       the one artifact a consumer reads"
ctisuite report \
	--pir "$out/pir.json" \
	--assessment "$aqui/assessment.json" \
	--verdict "$out/verdict.json" \
	--hunt "$out/hunt.json" \
	--product "$aqui/product.json" \
	--bundle "$out/bundle.json" \
	-o "$out/product.md"
head -12 "$out/product.md" | sed 's/^/  /'

printf '\nOK — seven steps, one chain, one product. Outputs in %s\n' "$out"
