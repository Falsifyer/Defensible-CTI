"""Graded linkage graph and threshold clustering."""

from __future__ import annotations

from dataclasses import dataclass, field

from cryptonym.model.confidence import Confidence

#: Ordinal rank used for thresholding. Confidence is ordered here, but it is *not*
#: summable: see ``Reconciliation.weakest_link``.
_RANK = {Confidence.LOW: 1, Confidence.MODERATE: 2, Confidence.HIGH: 3}


@dataclass(frozen=True)
class Linkage:
    """A graded edge between two designations.

    The edge is the hypothesis; the nodes are the vendor names. Nothing is merged by
    the mere existence of a linkage — the confidence decides what a threshold does
    with it.
    """

    left: str
    right: str
    confidence: Confidence
    assessment_id: str = ""


@dataclass
class Reconciliation:
    """A set of graded linkages, queryable at any confidence threshold."""

    linkages: list[Linkage] = field(default_factory=list)

    def edges_at(self, minimum: Confidence) -> list[Linkage]:
        """Linkages asserted at or above ``minimum`` confidence."""
        floor = _RANK[minimum]
        return [link for link in self.linkages if _RANK[link.confidence] >= floor]

    def clusters(self, minimum: Confidence) -> list[set[str]]:
        """Connected components over linkages at or above ``minimum`` confidence.

        Clusters are *computed*, so lowering the threshold can split them again — the
        underlying edges are never lost.
        """
        parent: dict[str, str] = {}

        def find(node: str) -> str:
            parent.setdefault(node, node)
            while parent[node] != node:
                parent[node] = parent[parent[node]]
                node = parent[node]
            return node

        def union(left: str, right: str) -> None:
            root_left, root_right = find(left), find(right)
            if root_left != root_right:
                parent[root_right] = root_left

        for link in self.edges_at(minimum):
            union(link.left, link.right)

        groups: dict[str, set[str]] = {}
        for node in list(parent):
            groups.setdefault(find(node), set()).add(node)
        return list(groups.values())

    def weakest_link(self, cluster: set[str]) -> Linkage | None:
        """The lowest-confidence linkage fully internal to ``cluster``."""
        internal = [link for link in self.linkages if link.left in cluster and link.right in cluster]
        if not internal:
            return None
        return min(internal, key=lambda link: _RANK[link.confidence])
