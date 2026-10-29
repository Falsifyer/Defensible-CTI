---
title: "El gate que se niega"
date: 2026-10-29
status: draft
tags: [cti, stix, tlp, seguridad]
---

> **Alcance:** prueba de concepto personal, no producción. El corpus es ilustrativo y no se
> afirma precisión del mundo real. Véase [`SCOPE.md`](../SCOPE.md).

Un producto de inteligencia no se comparte porque esté bien escrito. Se comparte porque
alguien puede decir **quién lo dice, cuándo y hasta dónde puede viajar**. Si falta una de
las tres, el gate debería negarse.

Este proyecto tiene un gate pequeño y deliberadamente aburrido: `sharegate`. No intenta
ser un DLP ni un validador completo de STIX. Comprueba dos cosas que sí son objetivas:

- **TLP 2.0** sobre las marcas que los objetos realmente referencian;
- **STIX 2.1** estructural, con un único validador compartido con la fábrica.

## Lo que encontré al auditarlo

Tres falsos permisos, todos reproducibles:

1. **Un producto sin `tlp` se construía como `TLP:CLEAR`**. El esquema decía que `tlp` era
   obligatorio, pero el código hacía `product.get("tlp") or "clear"`. Un olvido se
   convertía en publicación pública. Ahora se rechaza.
2. **Un bundle JSON corrupto se leía como texto**. Si `json.loads` fallaba, el gate caía al
   modo texto, veía “sin TLP” como un warning medio y devolvía `shareable: true`. Un bundle
   truncado pasaba. Ahora un `.json` ilegible es `checked: false` y exit 2.
3. **`ctisuite chain --out` hacía `rmtree` del destino sin guardas**. Un typo podía borrar
   el directorio de inputs o el home. Ahora rechaza inputs, cwd, home y ancestros; un
   destino no vacío exige `--force`.

## TLP 2.0, no un alias

Las marcas son los objetos oficiales de TLP 2.0. `TLP:WHITE` se reconoce solo para
marcarlo como obsoleto. Un bundle sin marca en un SDO de contenido es **high**, no un
warning. Eso incluye `infrastructure`, `note`, `attack-pattern` y `relationship`: la lista
blanca anterior los dejaba pasar.

La heurística de contenido sensible (IPs, emails, “victim”, “credentials”) sigue siendo
**medium** y no bloquea sola. Es un guard, no un clasificador; decirlo es parte del diseño.

## STIX sin caché

`stixforge validate --external` antes dependía de que `stix2-validator` hubiera descargado
sus esquemas. Sin caché devolvía 2; el CI solo hacía un parse de la librería y llamaba a
eso “external validation”.

Ahora los esquemas OASIS STIX 2.1 están **vendorizados** en el paquete (BSD-3, con
atribución) y la validación es offline:

```console
$ uv run stixforge build demo/product.json -o /tmp/bundle.json
$ uv run stixforge validate /tmp/bundle.json --external
External (schema): OASIS STIX 2.1 schemas (vendored) -> OK
```

El parse de `stix2` y el `stix2-validator` opcional se siguen reportando, pero el que
`--external` exige es el de los esquemas vendorizados.

## Qué no demuestra

Que un bundle sea válido, esté marcado y tenga trazas no significa que su contenido sea
cierto. El gate comprueba forma, marca y procedencia; no la calidad del análisis. Y la
heurística de sensibilidad puede fallar en ambos sentidos.

## Probarlo

```console
$ uv run sharegate policy
$ uv run sharegate check /tmp/bundle.json
$ uv run stixforge validate /tmp/bundle.json --external
```

Código y límites: [`SCOPE.md`](../SCOPE.md).
