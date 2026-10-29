# cti-suite
#
#   make install   creates the workspace environment with uv (all eight packages, editable)
#   make demo      runs the whole chain on fictional data
#   make test      every package's tests
#   make lint      ruff over the packages
#   make types     mypy over the packages
#   make eval      the method evaluation, against its baselines
#   make security  pip-audit over the environment
#   make build     builds the distributions
#   make clean     removes .venv, dist and the demo outputs

UV ?= uv

.PHONY: install demo test lint types eval security build clean

install:
	$(UV) sync --all-packages --all-extras

demo:
	$(UV) run sh demo/run.sh

test:
	$(UV) run pytest -q

lint:
	$(UV) run ruff check packages

types:
	$(UV) run mypy

eval:
	$(UV) run python packages/cryptonym/evaluation/run_evaluation.py --corpus --check
	$(UV) run python packages/cryptonym/evaluation/run_evaluation.py --adjudicated --check --strict

security:
	$(UV) run pip-audit --skip-editable --ignore-vuln PYSEC-2026-3447
	$(UV) run pip check

build:
	$(UV) build --all-packages --out-dir dist

clean:
	rm -rf .venv dist demo/out
