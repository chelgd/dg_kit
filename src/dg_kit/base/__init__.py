"""Shared base helpers used across ``dg_kit`` model layers."""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Literal


def add_value_to_indexed_list(index_dict: dict, key, value) -> None:
    if key in index_dict:
        index_dict[key].append(value)
    else:
        index_dict[key] = [value]


class DirectedAcyclicGraph:
    """Minimal DAG implementation with subgraph extraction by node id."""

    def __init__(self):
        self.nodes_by_id: dict[str, Any] = {}
        self.children_by_id: dict[str, set[str]] = defaultdict(set)
        self.parents_by_id: dict[str, set[str]] = defaultdict(set)

    def add_node(self, node_id: str, payload: Any = None) -> None:
        self.nodes_by_id[node_id] = payload
        self.children_by_id.setdefault(node_id, set())
        self.parents_by_id.setdefault(node_id, set())

    def add_edge(self, source_id: str, target_id: str) -> None:
        if source_id not in self.nodes_by_id or target_id not in self.nodes_by_id:
            raise KeyError(
                "Both source and target nodes must exist before adding an edge."
            )
        if source_id == target_id:
            raise ValueError("Self-loops are not allowed in a directed acyclic graph.")
        if source_id in self.descendants(target_id):
            raise ValueError(
                f"Adding edge '{source_id}' -> '{target_id}' would create a cycle."
            )

        self.children_by_id[source_id].add(target_id)
        self.parents_by_id[target_id].add(source_id)

    def descendants(self, node_id: str) -> set[str]:
        if node_id not in self.nodes_by_id:
            raise KeyError(f"Unknown node id: {node_id}")

        visited: set[str] = set()
        queue: deque[str] = deque(self.children_by_id[node_id])

        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            queue.extend(self.children_by_id[current])

        return visited

    def ancestors(self, node_id: str) -> set[str]:
        if node_id not in self.nodes_by_id:
            raise KeyError(f"Unknown node id: {node_id}")

        visited: set[str] = set()
        queue: deque[str] = deque(self.parents_by_id[node_id])

        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            queue.extend(self.parents_by_id[current])

        return visited

    def subgraph(
        self,
        node_id: str,
        direction: Literal["downstream", "upstream", "both"] = "both",
        include_root: bool = True,
    ) -> "DirectedAcyclicGraph":
        if node_id not in self.nodes_by_id:
            raise KeyError(f"Unknown node id: {node_id}")

        node_ids: set[str] = set()
        if include_root:
            node_ids.add(node_id)

        if direction in ("downstream", "both"):
            node_ids.update(self.descendants(node_id))
        if direction in ("upstream", "both"):
            node_ids.update(self.ancestors(node_id))

        subgraph = DirectedAcyclicGraph()
        for graph_node_id in node_ids:
            subgraph.add_node(graph_node_id, self.nodes_by_id[graph_node_id])

        for source_id in node_ids:
            for target_id in self.children_by_id[source_id]:
                if target_id in node_ids:
                    subgraph.add_edge(source_id, target_id)

        return subgraph

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [
                {
                    "id": node_id,
                    "payload": self.nodes_by_id[node_id],
                }
                for node_id in self.nodes_by_id
            ],
            "edges": [
                {
                    "source_id": source_id,
                    "target_id": target_id,
                }
                for source_id, children in self.children_by_id.items()
                for target_id in children
            ],
        }
