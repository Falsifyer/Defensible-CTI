"""HuntPlan — turn a question into a falsifiable hunt plan.

A hunt starts from a hypothesis, not from a tool. This package forces the hypothesis to
be falsifiable (If … then …), to name the telemetry that would satisfy it, and to carry a
**closure criterion** — when the hunt is done, and what "not found" means. Maturity is
assessed against the Hunting Maturity Model, not against enthusiasm.
"""

__version__ = "0.1.0"
