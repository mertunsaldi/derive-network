# Contributing

Thank you for contributing to Derivation Network!

## Development Workflow

1. Install dependencies via `make install`.
2. Run `make lint` and `make test` before committing.
3. Use feature branches and submit pull requests.
4. Ensure documentation (README, API docs, architecture) stays up to date.

## Code Style

- Python: follow Ruff + MyPy (strict). Type hints are mandatory.
- TypeScript: use strict mode (`tsconfig.json`).
- Commit messages should follow Conventional Commits when possible.

## Testing

- `pytest` provides unit and API tests using the in-memory `GraphStore`.
- Add tests alongside new functionality.

## Continuous Integration

GitHub Actions automatically runs linting, typing, and tests on each pull request and on pushes to `main`.

## Reporting Issues

Create a GitHub issue with a clear description, reproduction steps, and expected behaviour.
