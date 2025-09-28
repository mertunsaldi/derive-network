from __future__ import annotations

import networkx as nx
import pytest

from examples.seed_data import load_seed_graph


def test_seed_graph_paths() -> None:
    store = load_seed_graph()
    lookup = store.graph.graph["id_lookup"]
    energy_id = lookup["seed-energy"]
    work_energy_id = lookup["seed-work-energy"]
    path, _ = store.shortest_path(energy_id, work_energy_id)
    assert path[0] == energy_id
    assert path[-1] == work_energy_id


def test_preference_filtering_blocks_path() -> None:
    store = load_seed_graph()
    statements = [node for node, data in store.graph.nodes(data=True) if data.get("type") == "statement"]
    first = statements[0]
    last = statements[-1]
    with pytest.raises(nx.NetworkXNoPath):
        store.shortest_path(first, last, preferences=["nonexistent-rule"])
