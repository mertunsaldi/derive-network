# Derivation Network Monorepo

Derivation Network is a STEM knowledge graph that stores canonical statements (formulae, theorems, laws) and their derivations. Statements are normalised to SymPy canonical forms, hashed for deduplication, and linked through typed derivation hyperedges.

## Quickstart

### Prerequisites

- Python 3.11
- Poetry 1.7+
- Docker (for local Neo4j + services)
- Node.js 20+ (optional, to run the viewer outside Docker)

### Install dependencies

```bash
make install
```

### Run tests

```bash
make test
```

### Lint and type-check

```bash
make lint
```

### Seed local data

```bash
make seed
```

### Launch the stack

```bash
make up
```

The stack exposes:

- API Gateway: http://localhost:8000
- Neo4j Browser: http://localhost:7474
- Viewer (Vite): http://localhost:5173

Use `make down` to stop all containers.

## Repository Layout

```
services/
  api/             # FastAPI gateway
  canonicalizer/   # Canonicalisation microservice
  graphstore/      # Graph store microservice facade
web/viewer/        # Cytoscape + MathJax viewer (Vite + TypeScript)
infra/             # docker-compose + Neo4j configuration
schemas/           # Shared Pydantic models and OpenAPI helpers
examples/          # Seed data and scripts
src/derive_network # Core Python package
```

Additional documentation:

- [ARCHITECTURE.md](ARCHITECTURE.md) – system overview
- [API.md](API.md) – REST contract
- [CONTRIBUTING.md](CONTRIBUTING.md) – development workflow

## Development Notes

- All Python code is typed and checked with `mypy --strict`.
- `ruff` enforces formatting and linting.
- FastAPI automatically exposes OpenAPI docs at `/docs`.
- Tests use the in-memory `GraphStore` (NetworkX) to avoid Neo4j dependency during CI.
