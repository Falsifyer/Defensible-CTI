---
title: "Una nota es una afirmación sobre la evidencia"
date: 2026-10-29
status: draft
tags: [cti, analisis, ach, incertidumbre]
---

> **Alcance:** esto describe una prueba de concepto personal, no un sistema de producción.
> El corpus es ilustrativo y no se afirma precisión del mundo real. Véase
> [`SCOPE.md`](../SCOPE.md).

En CTI, “confianza alta” suele ser una palabra que alguien escribe en un campo. No dice
qué la sostiene, no dice qué la rompería y no dice si dos fuentes son dos o una repetida.

La idea de este proyecto es simple: **una nota es una afirmación sobre la evidencia, así que
la evidencia pone un techo**. El analista puede declarar menos; no puede declarar más.

## El techo

En el motor hay tres niveles:

| Techo | Requisito |
|---|---|
| `low` | nada diagnóstico discrimina: tradecraft compartido, lenguaje de proveedor, solapamiento estructural |
| `moderate` | al menos un ítem diagnóstico discrimina, todo desde una fuente |
| `high` | al menos un ítem diagnóstico discrimina **y** dos fuentes independientes aportan diagnósticos |

“Diagnóstico” no es “lo que suena a evidencia”. En una pregunta de identidad, solo
`infrastructure`, `code` y `operator` pueden sostener una llamada. `tactics`, `linguistic`,
`structural` y `open_source` explican y contradicen, pero no bastan por sí solos.

Además, una hipótesis necesita **soporte positivo**: al menos un ítem diagnóstico
consistente con ella. Si solo tiene consistencia lingüística, se marca
`consistent_but_unsupported` y no puede ser la favorita. “Menos contradicciones” no es
“más apoyo”.

## Por qué importa

Tomemos un dossier con diez ítems. Ocho son lenguaje de proveedor y tradecraft compartido;
uno es una infraestructura que no distingue; uno es una pieza de código que sí. Sin la
regla, el dossier puede imprimir “moderada” porque hay mucha tinta. Con la regla, el techo
lo pone el único ítem que puede distinguir algo.

El ejemplo público del repositorio, VOLTZITE vs Volt Typhoon, terminó mostrando algo
incómodo: la hipótesis “same actor” tenía **0.5 de contradicción de identidad y 1.5 de
contexto**, y ningún soporte diagnóstico. El motor ya no la presenta como favorita; dice
que está addressed but unsupported.

## Dos ejes, no uno

La confianza no es la probabilidad. Un claim puede ser *muy probable* con *baja* confianza
(una sola fuente) o *incierto* con *alta* confianza (buenos datos, genuinely ambiguous).
El proyecto separa:

- `confidence`: calidad de las fuentes y del razonamiento;
- `probability`: probabilidad del resultado estimado;
- `probability_of`: la proposición sobre la que se hace la probabilidad.

Sin `probability_of`, “unlikely” junto a “favoured: distinct_but_overlapping” se puede leer
como lo contrario. La etiqueta ahora dice “probability that same_actor is true: unlikely”.

## Claim mode no es una puerta trasera

Un hecho documental (“MITRE registra C0029 como campaña”) no es una disputa entre
alternativas. Para eso existe `mode: "claim"`. Pero el modo es explícito y tiene guardas:

- `claim_type`: `documentary`, `estimative` o `identity`;
- `why_no_alternatives` obligatorio;
- `direct` solo para `documentary`;
- una pregunta de identidad o atribución en `claim` es un finding high.

Si no, bastaría declarar una hipótesis y dos ítems `direct` para saltarse el ACH.

## Qué no demuestra

Que el motor sea coherente con la evidencia declarada no significa que la evidencia sea
verdadera, completa o independiente. Las fuentes y la matriz las escribe un analista. El
techo comprueba la relación entre la nota y lo que se le dio; no sustituye la recolección
ni la verificación.

## Probarlo

```console
$ uv run assessment assess demo/assessment.json
$ uv run assessment assess demo/assessment.json --strict
$ uv run cryptonym render packages/cryptonym/assessments/voltzite-vs-volt-typhoon/assessment.json
```

Código y limitaciones: [`SCOPE.md`](../SCOPE.md).
