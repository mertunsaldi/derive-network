from __future__ import annotations

import logging
from uuid import uuid4
from typing import List, Optional

import networkx as nx
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from derive_network import (
    Canonicalizer,
    Derivation,
    DerivationCreate,
    GraphStore,
    PathResponse,
    Statement,
    StatementCreate,
)

logger = logging.getLogger(__name__)

app = FastAPI(title="Derivation Network API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CANONICALIZER = Canonicalizer()
GRAPH_STORE = GraphStore()


def get_graph_store() -> GraphStore:
    return GRAPH_STORE


def get_canonicalizer() -> Canonicalizer:
    return CANONICALIZER


@app.post("/v1/statements", response_model=Statement)
async def create_statement(
    payload: StatementCreate,
    canonicalizer: Canonicalizer = Depends(get_canonicalizer),
    store: GraphStore = Depends(get_graph_store),
) -> Statement:
    if not payload.latex and not payload.sympy:
        raise HTTPException(status_code=400, detail="One of latex or sympy is required")
    result = canonicalizer.canonicalize(
        latex=payload.latex,
        sympy_str=payload.sympy,
        assumptions=payload.assumptions,
        regime=payload.regime,
        field_tags=payload.field_tags,
        sources=payload.sources,
        confidence=payload.confidence,
    )
    statement = store.add_statement(result.statement)
    return statement


@app.get("/v1/statements/{statement_id}", response_model=Statement)
async def get_statement(statement_id: str, store: GraphStore = Depends(get_graph_store)) -> Statement:
    statement = store.get_statement(statement_id)
    if not statement:
        raise HTTPException(status_code=404, detail="Statement not found")
    return statement


@app.post("/v1/derivations", response_model=Derivation)
async def create_derivation(
    payload: DerivationCreate,
    store: GraphStore = Depends(get_graph_store),
) -> Derivation:
    missing: List[str] = [sid for sid in payload.inputs if not store.get_statement(sid)]
    missing += [sid for sid in payload.outputs if not store.get_statement(sid)]
    if missing:
        raise HTTPException(status_code=400, detail=f"Unknown statement ids: {', '.join(sorted(set(missing)))}")
    derivation = Derivation(
        id=f"deriv-{uuid4().hex}",
        rule_tags=list(payload.rule_tags),
        exact=payload.exact,
        error_bound=payload.error_bound,
        script_ref=payload.script_ref,
        assumptions=list(payload.assumptions),
        sources=list(payload.sources),
    )
    store.add_derivation(derivation, inputs=payload.inputs, outputs=payload.outputs)
    return derivation


@app.get("/v1/derivations/{derivation_id}", response_model=Derivation)
async def get_derivation(derivation_id: str, store: GraphStore = Depends(get_graph_store)) -> Derivation:
    derivation = store.get_derivation(derivation_id)
    if not derivation:
        raise HTTPException(status_code=404, detail="Derivation not found")
    return derivation


@app.get("/v1/paths", response_model=PathResponse)
async def get_path(
    src: str = Query(..., description="Source statement id"),
    dst: str = Query(..., description="Destination statement id"),
    preferences: Optional[str] = Query(None, description="Comma-separated rule tags"),
    store: GraphStore = Depends(get_graph_store),
) -> PathResponse:
    try:
        preference_list = preferences.split(",") if preferences else None
        path, nodes = store.shortest_path(src, dst, preferences=preference_list)
    except nx.NetworkXNoPath as exc:
        raise HTTPException(status_code=404, detail="No path found") from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return PathResponse(path=path, nodes=nodes)


@app.get("/healthz")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
