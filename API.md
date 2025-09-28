# API Overview

Base URL: `/v1`

## POST /v1/statements

Create or retrieve a canonical statement.

### Request Body

```
{
  "latex": "K = \\frac{1}{2} m v^2", // optional
  "sympy": "K - 1/2*m*v**2",       // optional
  "assumptions": ["m>0"],           // optional
  "regime": ["non-relativistic"],   // optional
  "field_tags": ["mechanics"],      // optional
  "sources": ["classical-mechanics"],
  "confidence": "unchecked"         // enum: unchecked|cas|formal
}
```

One of `latex` or `sympy` is required.

### Response

```
{
  "id": "<sha256>",
  "latex_variants": ["K = \\frac{1}{2} m v^2"],
  "sympy_srepr": "Add(Mul(...))",
  "assumptions": ["m>0"],
  "units": {"m": 0.0, "kg": 0.0, ...},
  "regime": ["non-relativistic"],
  "field_tags": ["mechanics"],
  "sources": ["classical-mechanics"],
  "confidence": "unchecked"
}
```

## GET /v1/statements/{id}

Retrieve a statement by identifier.

## POST /v1/derivations

Create a derivation hyperedge.

### Request Body

```
{
  "inputs": ["<statement-id>"],
  "outputs": ["<statement-id>"],
  "rule_tags": ["algebra"],
  "exact": true,
  "error_bound": null,
  "script_ref": "s3://...",
  "assumptions": [],
  "sources": []
}
```

### Response

```
{
  "id": "deriv-<uuid>",
  "rule_tags": ["algebra"],
  "exact": true,
  "error_bound": null,
  "script_ref": "s3://...",
  "created_at": "2024-01-01T00:00:00Z",
  "assumptions": [],
  "sources": []
}
```

## GET /v1/derivations/{id}

Retrieve derivation metadata.

## GET /v1/paths

Find the shortest path between two statements. Optional `preferences` limits derivations to those containing the given rule tags.

### Query Parameters

- `src` – source statement id (required)
- `dst` – destination statement id (required)
- `preferences` – comma separated rule tags (optional)

### Response

```
{
  "path": ["<node-id>", ...],
  "nodes": {
    "<node-id>": {"type": "statement", "data": {...}},
    "<node-id>": {"type": "derivation", "data": {...}}
  }
}
```

## Health Check

`GET /healthz` returns `{ "status": "ok" }`.
