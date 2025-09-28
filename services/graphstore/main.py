from __future__ import annotations

from fastapi import FastAPI, HTTPException

from derive_network import DerivationCreate, GraphStore

app = FastAPI(title="Graph Store Service", version="0.1.0")
STORE = GraphStore()


@app.get("/graph/{node_id}")
async def get_node(node_id: str) -> dict[str, object]:
    node = STORE.graph.nodes.get(node_id)
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    return {"type": node.get("type"), "data": node.get("data", {})}


@app.post("/graph/derivations")
async def add_derivation(payload: DerivationCreate) -> dict[str, object]:
    raise HTTPException(status_code=501, detail="Use the API gateway service")
