"""Official TLP markings, taken from the STIX 2.1 specification.

The specification (OASIS, 2.1 OS) still carries the four TLP 1.0 markings, with their
canonical identifiers and names. TLP 2.0 (FIRST) renamed ``white`` to ``clear`` and added
``amber+strict``, but those marking-definition objects are not in the specification's
appendix, so this tool maps ``clear`` to the spec's object and says so in the README rather
than inventing identifiers.
"""

from __future__ import annotations

# id, name, created — exactly as published in the STIX 2.1 specification.
MARKINGS: dict[str, tuple[str, str, str]] = {
    "white": ("marking-definition--613f2e26-407d-48c7-9eca-b8e91df99dc9", "TLP:WHITE", "2017-01-20T00:00:00.000Z"),
    "green": ("marking-definition--34098fce-860f-48ae-8e50-ebd3cc5e41da", "TLP:GREEN", "2017-01-20T00:00:00.000Z"),
    "amber": ("marking-definition--f88d31f6-486f-44da-b317-01333bde0b82", "TLP:AMBER", "2017-01-20T00:00:00.000Z"),
    "red": ("marking-definition--5e57c739-391a-4eb3-b6be-7d15ca92d5ed", "TLP:RED", "2017-01-20T00:00:00.000Z"),
}

# TLP 2.0 name -> marking this tool emits.
ALIASES = {"clear": "white", "white": "white", "green": "green", "amber": "amber", "red": "red"}


def marking_object(nombre: str) -> dict:
    """Return the marking-definition object for ``nombre`` (TLP 2.0 or 1.0 name)."""
    clave = ALIASES.get(nombre.lower().strip())
    if clave is None:
        raise ValueError(f"unknown TLP marking: {nombre!r}")
    ident, etiqueta, creado = MARKINGS[clave]
    return {
        "type": "marking-definition",
        "spec_version": "2.1",
        "id": ident,
        "created": creado,
        "definition_type": "tlp",
        "name": etiqueta,
        "definition": {"tlp": clave},
    }
