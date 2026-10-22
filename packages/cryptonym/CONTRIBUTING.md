# Contributing to Cryptonym

Contributions are welcome — new ingest adapters, exporters, better ACH scoring, and
documented case studies.

## Getting started

```bash
git clone https://github.com/ME0094/cryptonym.git
cd cryptonym
pip install -r requirements-dev.txt
```

## Running the checks

```bash
pytest --cov --cov-branch
ruff check .
bandit -q -r src
python evaluation/run_evaluation.py --dossier assessments/voltzite-vs-volt-typhoon/assessment.json
```

## Submitting changes

1. Fork the repo and branch from `main`.
2. Keep changes focused — one logical change per pull request.
3. Add or update tests for any behaviour change in `model/`, `assess/` or `reconcile/`.
4. Do not weaken the method for convenience: a change that lets evidence merge
   designations without diagnostic support will be rejected. See `docs/method.md`.
5. Never attach proprietary indicators, victim data, or sensitive source material.
