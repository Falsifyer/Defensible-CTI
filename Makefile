# cti-suite
#
#   make install   crea el entorno del workspace con uv (los ocho paquetes en editable)
#   make demo      corre la cadena completa sobre datos ficticios
#   make test      pruebas de todos los paquetes
#   make lint      ruff sobre los paquetes
#   make types     mypy sobre los paquetes
#   make eval      la evaluacion del metodo, contra sus baselines
#   make build     construye las distribuciones
#   make clean     borra .venv, dist y las salidas de la demo

UV ?= uv

.PHONY: install demo test lint types eval build clean

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

build:
	$(UV) build --all-packages --out-dir dist

clean:
	rm -rf .venv dist demo/out
