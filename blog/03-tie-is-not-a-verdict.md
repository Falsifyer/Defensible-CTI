---
title: "Un empate no es un veredicto"
date: 2026-10-29
status: draft
tags: [cti, ach, analisis, evaluacion]
---

> **Alcance:** prueba de concepto personal, no producción. El corpus es ilustrativo y no se
> afirma precisión del mundo real. Véase [`SCOPE.md`](../SCOPE.md).

Durante meses, el corpus de evaluación de este proyecto dio un resultado impecable:
0 falsos merge, 0 falsos split, accuracy del 100 %. Cuando fui a mirar por qué, el motor no
era tan bueno: el empate lo decidía **el orden en que el analista había escrito las
hipótesis**.

## El bug

El ranking ACH ordenaba por inconsistencia ponderada y, en caso de empate, por el índice de
la lista. Si `distinct_but_overlapping` y `brokered_shared_access` empataban a cero, ganaba
la primera. Reordenar las hipótesis cambiaba la conclusión sin tocar una sola pieza de
evidencia.

La corrección no es “desempatar mejor”. Es **no presentar un empate como una conclusión**:

- `tied` contiene las hipótesis que comparten el mejor resultado;
- `favoured` es `null` si hay más de una;
- el techo es el más restrictivo de las empatadas;
- el evaluador no puntúa un empate que incluye `same_actor`: lo cuenta como abstención.

## El segundo problema: la hipótesis que flota

El modelo incluía `brokered_shared_access` por defecto. Si ningún ítem la contradecía,
quedaba a cero y empataba con todo. El motor no podía distinguir “no hay evidencia de
broker” de “hay evidencia de que no hay broker”.

Ahora `brokered` es **opt-in**: el dossier lo declara cuando la evidencia sugiere un
broker. Por defecto se comparan `same_actor` y `distinct_but_overlapping`. Además, una
hipótesis necesita **soporte diagnóstico** (`infrastructure`, `code`, `operator`), no solo
consistencia lingüística.

## Lo que dijo el corpus después

Con estas reglas, el corpus ilustrativo pasó a:

```text
24 casos
23 llamadas
1 abstención
1 unsupported
11 verdaderos positivos / 12 verdaderos negativos
0 falsos merge / 0 falsos split
Brier 0.0775 sobre 23 llamadas
```

Ese “23 / 1 / 1” es el resultado. No es un “accuracy” universal; es lo que el motor decidió
sobre un corpus pequeño y sintético. Una abstención es un resultado, no un fallo que haya
que esconder.

## Ranking con dos capas

El otro cambio fue separar **identidad** (`infrastructure`, `code`, `operator`) de
**contexto** (`tactics`, `linguistic`, `structural`, `open_source`). El ranking es:

```text
addressed > supported > identity inconsistency > context inconsistency > voices
```

Una contradicción lingüística ya no puede pesar más que una de infraestructura. El veredicto
incluye `ranking_basis` para que el lector vea con qué se decidió. En el dossier VOLTZITE,
`same_actor` muestra 0.5 de contradicción de identidad y 1.5 de contexto: exactamente el
problema que el ranking anterior ocultaba.

## Qué no demuestra

Que el motor ya no decida por orden no significa que la evidencia sea buena. Las fuentes,
la independencia y la matriz siguen siendo declaradas. El corpus externo con adjudicadores
independientes es un andamiaje, no un resultado.

## Probarlo

```console
$ uv run cryptonym assess packages/cryptonym/assessments/voltzite-vs-volt-typhoon/assessment.json
$ uv run python packages/cryptonym/evaluation/run_evaluation.py --corpus --check
```

Código y límites: [`SCOPE.md`](../SCOPE.md).
