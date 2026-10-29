---
title: "Audité mi propio repositorio y encontré tres falsos permisos"
date: 2026-10-29
status: draft
tags: [cti, auditoria, ingenieria, stix]
---

> **Alcance:** prueba de concepto personal, no producción. No se usan datos, código ni
> infraestructura de un empleador. Véase [`SCOPE.md`](../SCOPE.md).

La parte incómoda de auditar tu propio proyecto no es encontrar bugs. Es encontrar que los
bugs contradicen exactamente la promesa del proyecto.

La promesa era: **“la herramienta se niega”**. El gate no deja pasar un bundle sin marca;
el motor no acepta una nota por encima de su evidencia. La auditoría encontró tres formas
de que sí lo hiciera.

## 1. Un producto sin TLP se publicaba como CLEAR

El esquema decía que `tlp` era obligatorio. El código hacía:

```python
marking = marking_object(product.get("tlp") or "clear")
```

Un producto sin marca se construía como `TLP:CLEAR`, y el gate lo declaraba compartible.
El olvido se convertía en publicación pública. Ahora `tlp` es obligatorio y el build falla.

## 2. Un bundle corrupto pasaba como texto

`sharegate` hacía `json.loads`; si fallaba, seguía con el modo texto. Un `.json` truncado
no era “un bundle inválido”: era “un producto sin TLP”, que era un warning medio. Salía
`shareable: true`, exit 0.

Ahora un `.json` ilegible es `checked: false` y exit 2. No se puede comprobar no es lo
mismo que está limpio.

## 3. `--out` borraba el destino

`ctisuite chain --out` hacía `shutil.rmtree(target)` sin guardas. Un typo en la ruta podía
borrar el directorio de inputs o el home. Ahora se rechazan inputs, cwd, home y ancestros;
un destino no vacío exige `--force`.

## Lo que también estaba mal

La auditoría encontró más:

- `assessment assess --strict` fallaba contra su propio esquema (`grade_findings`);
- el ledger no detectaba un truncado de cola;
- el ranking ACH desempataba por orden de lista;
- el gate no marcaba `infrastructure`, `note` o `relationship`;
- `snapshot_source` del MCP aceptaba `allow_private=True`, un SSRF al alcance del agente;
- `--external` salía 0 aunque el validador de esquemas no hubiera comprobado nada;
- las acciones de GitHub no estaban pinneadas a SHA;
- el `uv.lock` estaba desincronizado y el CI lo ocultaba con `uv sync`.

No todo se arregló el mismo día, pero cada hallazgo tiene un test de regresión y un commit.

## La lección

Los tests unitarios no encuentran falsos permisos. Encontrarlos requiere **probar el
sistema como un adversario**:

- ¿qué pasa si falta un campo que el esquema dice obligatorio?
- ¿qué pasa si el JSON está truncado?
- ¿qué pasa si el destino es el directorio equivocado?
- ¿qué pasa si el atacante controla el orden de una lista?
- ¿qué pasa si el verificador no tiene su ancla?

Un test que solo comprueba el camino feliz confirma que el código hace lo que escribiste,
no que se niegue a lo que promete negarse.

## Qué no demuestra

Que estos tres falsos permisos estén cerrados no significa que no haya otros. La auditoría
fue dirigida, no un fuzzing completo. El corpus sigue siendo ilustrativo y el motor sigue
sin atribuir.

## Probarlo

```console
$ uv run pytest -q
$ uv run stixforge build /tmp/no-tlp.json -o /tmp/x.json    # debe fallar
$ uv run sharegate check /tmp/corrupt.json                  # debe salir 2
```

Código y límites: [`SCOPE.md`](../SCOPE.md).
