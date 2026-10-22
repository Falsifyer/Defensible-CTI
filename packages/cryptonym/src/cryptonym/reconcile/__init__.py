"""Reconciliation as a graded graph — never a destructive merge.

This is the part platforms get wrong. Storing aliases as a flat list collapses a
*hypothesis* into a *fact* the moment it is written, and the reasoning is lost forever.
Cryptonym keeps designations as nodes and assessments as graded edges, and computes
clusters only at an explicit confidence threshold. A cluster always reports its weakest
link, because a chain of ``same-as`` assertions is only as strong as its most poorly
evidenced edge and confidence does not multiply cleanly along a chain.
"""
