# Architecture

## Overview

Derivation Network is composed of three Python services and a TypeScript viewer:

- **Canonicalizer** – converts LaTeX or SymPy strings into canonical SymPy expressions, performs alpha-renaming and hashing, and emits statement metadata.
- **Graph Store** – wraps Neo4j (and provides an in-memory NetworkX fallback) to manage statements, derivations, and shortcut relationships.
- **API Gateway** – FastAPI application that orchestrates canonicalisation, graph persistence, queries, and path-finding.
- **Viewer** – Vite + Cytoscape.js front-end that visualises derivation paths and renders math with MathJax.

## Data Model

### Statement

| Field | Description |
| ----- | ----------- |
| `id` | SHA-256 hash of the canonical SymPy `srepr` plus sorted assumptions |
| `latex_variants` | List of submitted LaTeX representations |
| `sympy_srepr` | Canonical SymPy structural representation |
| `assumptions` | List of textual assumptions applied during canonicalisation |
| `units` | Mapping of SI base units to exponents |
| `regime` | Context labels (e.g. `non-relativistic`) |
| `field_tags` | STEM domains |
| `sources` | Bibliographic or URL references |
| `confidence` | Provenance (`unchecked`, `cas`, `formal`) |

### Derivation

| Field | Description |
| ----- | ----------- |
| `id` | UUID4-prefixed identifier |
| `rule_tags` | Derivation method tags |
| `exact` | `True` for exact derivations, `False` for approximations |
| `error_bound` | Optional textual error description |
| `script_ref` | Path/URL to derivation script |
| `assumptions` | Additional assumptions |
| `sources` | References |
| `created_at` | UTC timestamp assigned on creation |

### Relationships

- `Statement -[INPUT_OF]-> Derivation`
- `Derivation -[OUTPUT_OF]-> Statement`
- Shortcut relationships: `EQUIVALENT_TO`, `SPECIAL_CASE_OF`, `LIMIT_OF`, `APPROX_OF`, `REFORMULATION_OF`, `UNITS_TRANSFORM`, `ASSUMES`

Hyperedges are modelled via intermediate `Derivation` nodes so that multi-input/multi-output derivations are supported.

## Canonicalisation Pipeline

1. Parse LaTeX (via `sympy.parsing.latex`) or SymPy string (custom parser transformations).
2. Move all equations to the LHS and simplify to `expr = 0` form.
3. Expand commutative expressions, factor, and simplify.
4. Alpha-rename symbols to `x_i` to ensure structural equality.
5. Standardise gradient symbols (`∇`).
6. Compute unit exponents (stubbed to SI base vector where units are available).
7. Hash the canonical `srepr` together with assumptions to produce the statement identifier.

Equivalence checking first attempts symbolic simplification; if inconclusive, numeric probes are used.

## Graph Operations

- In-memory `GraphStore` uses NetworkX for unit tests and local reasoning.
- Neo4j integration is encapsulated so future work can swap the backend (e.g. TypeDB) without touching the API layer.
- Path-finding uses shortest path with optional rule-tag filtering.

## Deployment

- Docker Compose spins up Neo4j, the API service, and the viewer.
- CI runs linting, typing, and tests on every push/PR.
