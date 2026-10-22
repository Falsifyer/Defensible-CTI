"""Official TLP markings, re-exported from the shared core.

The table is the OASIS TLP 2.0 marking definitions, owned by :mod:`cti_method.stix` so the
factory and the gate read the same one. ``TLP:WHITE`` is deprecated and is not emitted.
"""

from __future__ import annotations

from cti_method.stix import TLP, TLP_EXTENSION_ID, label, marking_object

__all__ = ["TLP", "TLP_EXTENSION_ID", "label", "marking_object"]
