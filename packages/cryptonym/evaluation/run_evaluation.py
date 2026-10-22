"""Re-derive judgements and score the method, reproducibly.

Three modes:

* ``--dossier PATH`` — reproduce the single published judgement from the published
  evidence. CI fails if the method drifts from what was published.
* ``--corpus PATH`` — score the golden-pair corpus (development / held-out splits).
* ``--adjudicated PATH`` — score the **adjudicated** corpus through the external-truth
  filter: only cases whose truth is admissible enter the error rates; contested and
  unadjudicated cases are reported as coverage. ``--strict`` fails if a case claims a
  binary truth it did not earn.

The standard is described in ``docs/adjudication.md``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cryptonym.assess.grading import assess_actor_pair  # noqa: E402
from cryptonym.evaluate.adjudication import validate_corpus  # noqa: E402
from cryptonym.evaluate.metrics import evaluate_adjudicated, evaluate_corpus  # noqa: E402
from cryptonym.model.assessment import load_assessment  # noqa: E402

#: The judgement published in the worked example. If the engine stops reproducing it,
#: either the method changed (publish a new version) or it broke (fix it).
EXPECTED_FIRST_HYPOTHESIS = "distinct_but_overlapping"

EVAL_DIR = Path(__file__).resolve().parent
DEFAULT_CORPUS = EVAL_DIR / "golden_pairs" / "pairs.json"
DEFAULT_EXPECTED = EVAL_DIR / "golden_pairs" / "expected.json"
DEFAULT_ADJUDICATED = EVAL_DIR / "adjudicated" / "corpus.json"
DEFAULT_ADJUDICATED_EXPECTED = EVAL_DIR / "adjudicated" / "expected.json"


def _reproduce_dossier(path: str) -> int:
    result = assess_actor_pair(load_assessment(path))
    favoured = result["hypotheses_favoured"][0]
    if favoured != EXPECTED_FIRST_HYPOTHESIS:
        print(f"regression: expected {EXPECTED_FIRST_HYPOTHESIS!r}, got {favoured!r}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"# reproduced: {favoured}", file=sys.stderr)
    return 0


def _projection(summary: dict) -> dict:
    """The parts of a golden-pair summary that are committed as a baseline."""
    return {
        "overall": {
            "metrics": summary["overall"]["metrics"],
            "calibration": summary["overall"]["calibration"],
        },
        "splits": {
            name: {"metrics": data["metrics"], "calibration": data["calibration"]}
            for name, data in summary["splits"].items()
        },
    }


def _adjudicated_projection(summary: dict) -> dict:
    """The parts of an adjudicated summary that are committed as a baseline."""
    return {
        "metrics": summary["metrics"],
        "calibration": summary["calibration"],
        "coverage": summary["coverage"],
        "by_standard": summary["by_standard"],
    }


def _compare(projection: dict, expected: Path) -> int:
    baseline = json.loads(expected.read_text(encoding="utf-8"))
    if projection != baseline:
        print(f"regression: summary drifted from {expected.name}", file=sys.stderr)
        print(f"  expected: {json.dumps(baseline, sort_keys=True)}", file=sys.stderr)
        print(f"  actual:   {json.dumps(projection, sort_keys=True)}", file=sys.stderr)
        return 1
    print("# matches the committed expectation", file=sys.stderr)
    return 0


def _summarise(corpus: str, expected: str | None, check: bool, output: str | None) -> int:
    document = json.loads(Path(corpus).read_text(encoding="utf-8"))
    projection = _projection(evaluate_corpus(document))
    serialised = json.dumps(projection, indent=2, ensure_ascii=False, sort_keys=True)
    if output:
        Path(output).write_text(serialised + "\n", encoding="utf-8")
    print(serialised)

    overall = projection["overall"]["metrics"]
    print(
        f"# overall false_merge_rate={overall['false_merge_rate']} "
        f"false_split_rate={overall['false_split_rate']}",
        file=sys.stderr,
    )
    for name, data in projection["splits"].items():
        metrics = data["metrics"]
        print(
            f"# split {name}: n={metrics['total']} "
            f"false_merge_rate={metrics['false_merge_rate']} "
            f"false_split_rate={metrics['false_split_rate']}",
            file=sys.stderr,
        )
    if not check:
        return 0
    return _compare(projection, Path(expected or DEFAULT_EXPECTED))


def _adjudicated(path: str, expected: str | None, check: bool, strict: bool, output: str | None) -> int:
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    problems = validate_corpus(document)
    if problems:
        for problem in problems:
            print(f"invalid corpus: {problem}", file=sys.stderr)
        return 1

    summary = evaluate_adjudicated(document)
    projection = _adjudicated_projection(summary)
    serialised = json.dumps(projection, indent=2, ensure_ascii=False, sort_keys=True)
    if output:
        Path(output).write_text(serialised + "\n", encoding="utf-8")
    print(serialised)

    coverage = summary["coverage"]
    metrics = summary["metrics"]
    print(
        f"# coverage admissible={coverage['admissible']} "
        f"contested={coverage['contested']} unadjudicated={coverage['unadjudicated']}",
        file=sys.stderr,
    )
    print(
        f"# over admissible cases: false_merge_rate={metrics['false_merge_rate']} "
        f"false_split_rate={metrics['false_split_rate']}",
        file=sys.stderr,
    )

    if strict:
        unearned = [
            row
            for row in summary["results"]
            if row["declared_truth"] in ("same_actor", "distinct") and not row["admissible"]
        ]
        if unearned:
            for row in unearned:
                print(
                    f"strict: {row['id']} claims {row['declared_truth']} "
                    f"without earning it: {row['reasons']}",
                    file=sys.stderr,
                )
            return 1
        print("# strict: every binary truth is admissible", file=sys.stderr)

    if not check:
        return 0
    return _compare(projection, Path(expected or DEFAULT_ADJUDICATED_EXPECTED))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Re-derive and score Cryptonym's judgements.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dossier", help="Path to a single assessment JSON file.")
    group.add_argument("--corpus", nargs="?", const=str(DEFAULT_CORPUS), help="Path to a golden-pair corpus.")
    group.add_argument(
        "--adjudicated", nargs="?", const=str(DEFAULT_ADJUDICATED), help="Path to an adjudicated corpus."
    )
    parser.add_argument("--expected", help="Baseline to compare against with --check.")
    parser.add_argument("--check", action="store_true", help="Fail if the summary drifted.")
    parser.add_argument("--strict", action="store_true", help="Fail if a binary truth was not earned.")
    parser.add_argument("--output", help="Write the summary JSON to a file.")
    args = parser.parse_args(argv)

    if args.dossier:
        return _reproduce_dossier(args.dossier)
    if args.corpus:
        return _summarise(args.corpus, args.expected, args.check, args.output)
    return _adjudicated(args.adjudicated, args.expected, args.check, args.strict, args.output)


if __name__ == "__main__":
    raise SystemExit(main())
