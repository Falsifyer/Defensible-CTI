"""ShareGate — a pre-share compliance gate for CTI products.

Before a product or a STIX bundle leaves the building, two objective questions decide
whether it should: is the **TLP** marking correct, and is the **STIX** well-formed? Both
have external ground truth — the FIRST TLP 2.0 definitions and the STIX 2.1 specification —
so this tool is judged against a standard, not against an opinion.
"""

__version__ = "0.2.0"
