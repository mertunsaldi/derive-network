from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import networkx as nx

from .models import Derivation, Statement


class GraphEdgeType:
    INPUT_OF = "INPUT_OF"
    OUTPUT_OF = "OUTPUT_OF"
    EQUIVALENT_TO = "EQUIVALENT_TO"
    SPECIAL_CASE_OF = "SPECIAL_CASE_OF"
    LIMIT_OF = "LIMIT_OF"
    APPROX_OF = "APPROX_OF"
    REFORMULATION_OF = "REFORMULATION_OF"
    UNITS_TRANSFORM = "UNITS_TRANSFORM"
    ASSUMES = "ASSUMES"


@dataclass
class Relation:
    source: str
    target: str
    type: str
    attributes: Dict[str, object]


class GraphStore:
    """In-memory graph store emulating the Neo4j data model."""

    def __init__(self) -> None:
        self._graph = nx.MultiDiGraph()
        self._statements: Dict[str, Statement] = {}
        self._derivations: Dict[str, Derivation] = {}

    def add_statement(self, statement: Statement) -> Statement:
        existing = self._statements.get(statement.id)
        if existing:
            merged = existing.model_copy(update={
                "latex_variants": sorted(set(existing.latex_variants + statement.latex_variants)),
                "regime": sorted(set(existing.regime + statement.regime)),
                "field_tags": sorted(set(existing.field_tags + statement.field_tags)),
                "sources": sorted(set(existing.sources + statement.sources)),
            })
            self._statements[statement.id] = merged
            self._graph.nodes[statement.id]["data"] = merged.model_dump()
            return merged
        self._statements[statement.id] = statement
        self._graph.add_node(statement.id, type="statement", data=statement.model_dump())
        return statement

    def get_statement(self, statement_id: str) -> Optional[Statement]:
        return self._statements.get(statement_id)

    def add_derivation(
        self,
        derivation: Derivation,
        *,
        inputs: Sequence[str],
        outputs: Sequence[str],
    ) -> Derivation:
        self._derivations[derivation.id] = derivation
        self._graph.add_node(derivation.id, type="derivation", data=derivation.model_dump())
        for statement_id in inputs:
            if statement_id not in self._statements:
                raise KeyError(f"Unknown statement id: {statement_id}")
            self._graph.add_edge(statement_id, derivation.id, type=GraphEdgeType.INPUT_OF)
        for statement_id in outputs:
            if statement_id not in self._statements:
                raise KeyError(f"Unknown statement id: {statement_id}")
            self._graph.add_edge(derivation.id, statement_id, type=GraphEdgeType.OUTPUT_OF)
        return derivation

    def get_derivation(self, derivation_id: str) -> Optional[Derivation]:
        return self._derivations.get(derivation_id)

    def add_relation(
        self,
        relation_type: str,
        source: str,
        target: str,
        *,
        attributes: Optional[Dict[str, object]] = None,
    ) -> None:
        if source not in self._graph:
            raise KeyError(f"Unknown source node: {source}")
        if target not in self._graph:
            raise KeyError(f"Unknown target node: {target}")
        self._graph.add_edge(source, target, type=relation_type, **(attributes or {}))

    def shortest_path(
        self,
        source: str,
        target: str,
        *,
        preferences: Optional[Sequence[str]] = None,
    ) -> Tuple[List[str], Dict[str, Dict[str, object]]]:
        if source not in self._graph or target not in self._graph:
            raise KeyError("Source or target not found in graph")
        relevant_nodes = self._filter_nodes_by_preferences(preferences)
        subgraph = self._graph.subgraph(relevant_nodes).copy()
        path = nx.shortest_path(subgraph, source=source, target=target)
        node_data = {
            node: dict(self._graph.nodes[node]) for node in path
        }
        return path, node_data

    def _filter_nodes_by_preferences(self, preferences: Optional[Sequence[str]]) -> List[str]:
        if not preferences:
            return list(self._graph.nodes)
        preferred = set(preferences)
        selected: List[str] = []
        for node, data in self._graph.nodes(data=True):
            if data.get("type") != "derivation":
                selected.append(node)
                continue
            derivation = self._derivations[node]
            if preferred.issubset(set(derivation.rule_tags)):
                selected.append(node)
        return selected

    @property
    def graph(self) -> nx.MultiDiGraph:
        return self._graph


__all__ = ["GraphStore", "GraphEdgeType", "Relation"]
