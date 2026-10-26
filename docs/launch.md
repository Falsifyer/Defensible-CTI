# Launch

Everything needed to publish this repository without overclaiming. The code is ready; what
follows is the framing, the demo, and the announcement.

## One line

> A CTI tool suite that refuses: a requirement with no decision, a grade above its evidence,
> a bundle that does not say how far it may travel.

## The frame

**Reference implementation of an analytic method**, not a platform. The competitor is not
OpenCTI or MISP — those store and correlate; this one refuses. The competitor is the
spreadsheet, the `TLP:WHITE` copied from a template, and the confidence field someone typed.

Keep the scope in every sentence:

- **tested mechanism, not proven accuracy** — the corpus is illustrative and the README says so;
- **no support SLA** — issues are read, not promised;
- **MIT, no telemetry, no network on the default path.**

## The 90-second demo

Run it live or record it; the refusals are the memorable part, not the passing tests.

```console
# 1. The door: a bundle is not shareable until it says how far it travels
$ uv run stixforge build demo/product.json -o /tmp/bundle.json
$ uv run sharegate check /tmp/bundle.json

# 2. A clear bundle of IOCs is not a leak; a deprecated alias is refused
$ sed 's/"tlp": "amber"/"tlp": "clear"/' demo/product.json > /tmp/clear.json
$ uv run stixforge build /tmp/clear.json -o /tmp/clear-bundle.json
$ uv run sharegate check /tmp/clear-bundle.json      # exit 0: an IP is an indicator
$ sed 's/"tlp": "amber"/"tlp": "white"/' demo/product.json > /tmp/white.json
$ uv run stixforge build /tmp/white.json -o /tmp/w.json   # exit 1: TLP:WHITE is TLP 1.0
$ printf 'TLP:CLEAR\nTLP:RED\n' > /tmp/conflict.md
$ uv run sharegate check /tmp/conflict.md            # exit 1: conflicting markings

# 3. The ceiling: declaring more than the evidence supports is refused
$ uv run assessment assess demo/assessment.json --register demo/pir.json
$ python - <<'PY'
import json; d=json.load(open('demo/assessment.json')); d['judgement']['confidence']='high'
json.dump(d, open('/tmp/greedy.json','w'))
PY
$ uv run assessment assess /tmp/greedy.json          # exit 1: grade-exceeds-evidence

# 4. The chain
$ uv run ctisuite chain --dir demo
$ open demo/out/product.md
```

What to say while it runs, in one sentence per step: *who says it, how strong it is, what
would change it, and whether it may leave.*

## Announcement (English)

> I published cti-suite: a reference implementation of an analytic method for threat
> intelligence, in eight Python packages that run one cycle.
>
> The idea is simple and slightly uncomfortable: **a grade is a claim about evidence, so the
> evidence sets a ceiling on it.** `high` needs a diagnostic item that discriminates and two
> independent sources; shared tradecraft alone cannot exceed `low`. Declare more and the tool
> refuses, with exit code 1. A claim with no declared grade is refused too.
>
> The rest follows: a PIR must name the decision it informs; a hunt plan must be falsifiable
> and have a closure criterion; a STIX bundle must say who says it, when, and how far it may
> travel. The identifiers travel with the product as `<id>@<sha256:12>`, so a bundle can be
> walked back to the judgement and the requirement it came from.
>
> What it is not: a platform, a feed ingester, or an attribution engine. The corpus is
> illustrative and the README says so; real-world accuracy is not claimed.
>
> Two things I would value most: someone running the pre-share gate on a real bundle, and
> someone telling me where the ceiling rule is wrong.
>
> https://github.com/ME0094/cti-suite

## Do not claim

- that it attributes, or that it improves attribution accuracy;
- that the corpus proves the method;
- that it replaces OpenCTI, MISP or a SIEM;
- that it is production-supported.

## Publish checklist

- [x] No credentials, no absolute paths, no internal references (`git grep` audit).
- [x] MIT, `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `CITATION.cff`.
- [x] CI on 3.11/3.12/3.13, demo, evaluation, external STIX validation, build + wheel smoke.
- [x] README scoped: mechanism tested, accuracy not claimed.
- [ ] Repository public, description and topics set.
- [x] First green CI run on `main` (`9cbc380`).
- [x] PyPI publication ruled out: this repository is a test bench, so `publish.yml` stays a manual tool and no name is reserved (2026-10-26).
- [ ] One external user runs the gate; their bug list becomes the first issues.
- [ ] Article: "A grade is a claim about evidence — enforcing a ceiling in code".
- [ ] The old `ME0094/huntplan` gets the banner in `deprecation-huntplan.md`.

## After publishing

Measure the only thing that matters: **one external user, one issue about the method, one talk
or course that uses it.** Stars are not the metric. Review in six months: if none of the three
happened, keep the two packages that get used and archive the rest with the reason written
down.
