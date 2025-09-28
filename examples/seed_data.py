from __future__ import annotations

from typing import Sequence, TypedDict

from derive_network import Canonicalizer, GraphEdgeType, GraphStore, Derivation


class SeedFormula(TypedDict, total=False):
    id: str
    latex: str
    assumptions: Sequence[str]
    field_tags: Sequence[str]
    sources: Sequence[str]


class SeedDerivation(TypedDict, total=False):
    rule_tags: Sequence[str]
    inputs: Sequence[str]
    outputs: Sequence[str]
    exact: bool
    error_bound: str | None
    script_ref: str | None

SEED_FORMULAE: list[SeedFormula] = [
    {
        "id": "seed-energy",
        "latex": r"K = \frac{1}{2} m v^{2}",
        "assumptions": ["m>0", "v>=0"],
        "field_tags": ["mechanics"],
        "sources": ["classical-mechanics"],
    },
    {
        "id": "seed-energy-rate",
        "latex": r"\frac{dK}{dt} = F \cdot v",
        "field_tags": ["mechanics"],
    },
    {
        "id": "seed-work-energy",
        "latex": r"W = \Delta K",
        "field_tags": ["mechanics"],
    },
    {
        "id": "seed-div-curl",
        "latex": r"\nabla \cdot (\nabla \times A) = 0",
        "field_tags": ["vector-calculus"],
    },
    {
        "id": "seed-gauss-diff",
        "latex": r"\nabla \cdot E = \frac{\rho}{\varepsilon_0}",
        "field_tags": ["electromagnetism"],
    },
    {
        "id": "seed-gauss-integral",
        "latex": r"\oint_{\partial V} E \cdot dA = \frac{1}{\varepsilon_0} \int_V \rho dV",
        "field_tags": ["electromagnetism"],
    },
    {
        "id": "seed-small-angle",
        "latex": r"\sin(\theta) \approx \theta",
        "assumptions": ["|theta| < 0.1"],
        "field_tags": ["approximation"],
    },
]


SEED_DERIVATIONS: list[SeedDerivation] = [
    {
        "rule_tags": ["definition"],
        "inputs": ["seed-energy"],
        "outputs": ["seed-energy-rate"],
        "exact": True,
        "script_ref": "examples/work_energy.py",
    },
    {
        "rule_tags": ["work-energy"],
        "inputs": ["seed-energy-rate"],
        "outputs": ["seed-work-energy"],
        "exact": True,
    },
    {
        "rule_tags": ["vector-calculus"],
        "inputs": ["seed-div-curl"],
        "outputs": ["seed-gauss-diff"],
        "exact": True,
    },
    {
        "rule_tags": ["integral"],
        "inputs": ["seed-gauss-diff"],
        "outputs": ["seed-gauss-integral"],
        "exact": True,
    },
    {
        "rule_tags": ["approximation"],
        "inputs": ["seed-small-angle"],
        "outputs": ["seed-energy"],
        "exact": False,
        "error_bound": "O(theta^3)",
    },
]


def load_seed_graph() -> GraphStore:
    canonicalizer = Canonicalizer()
    store = GraphStore()
    id_lookup: dict[str, str] = {}
    for formula in SEED_FORMULAE:
        result = canonicalizer.canonicalize(
            latex=formula["latex"],
            sympy_str=None,
            assumptions=formula.get("assumptions", ()),
            field_tags=formula.get("field_tags", ()),
            sources=formula.get("sources", ()),
        )
        statement = result.statement
        store.add_statement(statement)
        id_lookup[formula["id"]] = statement.id
    for deriv in SEED_DERIVATIONS:
        inputs = [id_lookup[s] for s in deriv["inputs"]]
        outputs = [id_lookup[s] for s in deriv["outputs"]]
        from uuid import uuid4

        derivation = {
            "id": f"deriv-{uuid4().hex}",
            "rule_tags": deriv["rule_tags"],
            "exact": deriv.get("exact", True),
            "error_bound": deriv.get("error_bound"),
            "script_ref": deriv.get("script_ref"),
        }
        store.add_derivation(
            Derivation.model_validate(derivation),
            inputs=inputs,
            outputs=outputs,
        )
    # Shortcut relationships
    store.add_relation(
        GraphEdgeType.EQUIVALENT_TO,
        id_lookup["seed-gauss-diff"],
        id_lookup["seed-gauss-integral"],
        attributes={"notes": "Gauss theorem differential-integral equivalence"},
    )
    store.add_relation(
        GraphEdgeType.SPECIAL_CASE_OF,
        id_lookup["seed-energy"],
        id_lookup["seed-work-energy"],
        attributes={"context": "work-energy theorem"},
    )
    store.graph.graph["id_lookup"] = id_lookup
    return store


if __name__ == "__main__":
    store = load_seed_graph()
    print(f"Seeded {len(store.graph.nodes)} nodes and {len(store.graph.edges)} edges.")
