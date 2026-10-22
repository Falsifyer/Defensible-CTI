# cti-suite
#
#   make install   crea el entorno del workspace con uv (los seis paquetes en editable)
#   make demo      corre la cadena completa sobre datos ficticios
#   make test      pruebas de los seis paquetes
#   make lint       ruff sobre los seis paquetes
#   make clean     borra .venv y las salidas de la demo

UV ?= uv

.PHONY: install demo test lint clean

install:
	$(UV) sync --all-packages --all-extras

demo:
	$(UV) run sh demo/run.sh

test:
	@for p in packages/*; do echo "== $$p"; (cd $$p && $(UV) run pytest -q) || exit 1; done

lint:
	$(UV) run ruff check packages

clean:
	rm -rf .venv demo/out
