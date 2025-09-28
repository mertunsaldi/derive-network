.PHONY: install lint test up down seed

install:
poetry install

lint:
poetry run ruff check .
poetry run mypy -p derive_network -p services.api -p services.canonicalizer -p services.graphstore
poetry run mypy examples tests

test:
poetry run pytest

up:
docker compose -f infra/docker-compose.yml up --build

down:
docker compose -f infra/docker-compose.yml down

seed:
poetry run python examples/seed_data.py
