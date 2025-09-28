from __future__ import annotations

from fastapi import FastAPI, HTTPException

from derive_network import Canonicalizer, StatementCreate

app = FastAPI(title="Canonicalizer Service", version="0.1.0")
CANONICALIZER = Canonicalizer()


@app.post("/canonicalize")
async def canonicalize(payload: StatementCreate) -> dict[str, str]:
    if not payload.latex and not payload.sympy:
        raise HTTPException(status_code=400, detail="One of latex or sympy is required")
    result = CANONICALIZER.canonicalize(
        latex=payload.latex,
        sympy_str=payload.sympy,
        assumptions=payload.assumptions,
        regime=payload.regime,
        field_tags=payload.field_tags,
        sources=payload.sources,
        confidence=payload.confidence,
    )
    return {
        "id": result.statement.id,
        "sympy_srepr": result.sympy_srepr,
    }
