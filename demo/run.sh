#!/bin/sh
# The whole cycle, one command, fictional data.
#
#   make demo
#
# Six steps in the order the cycle runs, each consuming what the previous one produced: the
# requirement says what is worth answering, the judgement answers it, the ledger grades it, the
# hunt plan says what to look for, the product turns it into STIX, and the gate decides whether it
# may leave. Nothing here is real: NIGHTJAR and SALTWIND do not exist.

set -eu

aqui=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
out="$aqui/out"
mkdir -p "$out"

paso() { printf '\n== %s\n' "$1"; }

paso "1/6  pir validate      what is worth answering, and which decision it informs"
pir validate "$aqui/pir.json" | sed 's/^/  /'

paso "2/6  cryptonym assess   the judgment on the alias question"
cryptonym assess "$aqui/dossier.json" > "$out/judgement.json"
python3 - "$out/judgement.json" <<'PY'
import json, sys
j = json.load(open(sys.argv[1]))
print("  favoured    :", ", ".join(j.get("hypotheses_favoured", [])))
print("  discriminating:", ", ".join(j.get("discriminating_evidence", [])) or "none")
print("  grade       :", j.get("confidence"), "| probability:", j.get("probability"))
PY

paso "3/6  assessment assess  the same claim, graded in two axes and kept in the ledger"
assessment assess "$aqui/claim.json" > "$out/verdict.json"
python3 - "$out/verdict.json" <<'PY'
import json, sys
v = json.load(open(sys.argv[1])); g = v.get("grade", {})
print("  ranking     :", ", ".join(v.get("ranking", [])))
print("  confidence  :", g.get("confidence"), "| probability:", g.get("probability"))
PY

paso "4/6  huntplan validate  what we would hunt, and it has to be falsifiable"
huntplan validate "$aqui/hunt.txt" > "$out/hunt.json"
python3 - "$out/hunt.json" <<'PY'
import json, sys
h = json.load(open(sys.argv[1]))
print("  falsifiable :", h.get("falsifiable"))
for f in (h.get("findings") or [])[:3]:
    print(f"  {f['code']:18s} {f['message'][:70]}")
PY

paso "5/6  stixforge build    the product, as a STIX 2.1 bundle"
stixforge build "$aqui/product.json" -o "$out/bundle.json"
python3 - "$out/bundle.json" <<'PY'
import json, sys
b = json.load(open(sys.argv[1]))
print("  objects     :", len(b["objects"]))
print("  types       :", ", ".join(sorted({o["type"] for o in b["objects"]})))
PY

paso "6/6  sharegate check     may it leave, and how far"
if ! sharegate check "$out/bundle.json" > "$out/gate.json"; then
	echo "  THE GATE REFUSES: this bundle does not leave." >&2
	sed 's/^/  /' "$out/gate.json" >&2
	exit 1
fi
python3 - "$out/gate.json" <<'PY'
import json, sys
r = json.load(open(sys.argv[1]))
print("  shareable   :", r.get("shareable"))
print("  effective   :", r.get("effective_tlp"), "| clean:", r["tlp"]["clean"])
print("  stix valid  :", r["stix"]["valid"])
PY

printf '\nOK — the six tools run as one chain. Outputs in %s\n' "$out"
