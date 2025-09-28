from __future__ import annotations

from fastapi.testclient import TestClient

from derive_network import Canonicalizer, GraphStore
from services.api import main as api_main


def setup_module() -> None:
    api_main.GRAPH_STORE = GraphStore()
    api_main.CANONICALIZER = Canonicalizer()


def test_statement_lifecycle() -> None:
    setup_module()
    client = TestClient(api_main.app)

    response = client.post("/v1/statements", json={"sympy": "K - 1/2*m*v**2"})
    assert response.status_code == 200
    statement = response.json()
    statement_id = statement["id"]

    response = client.get(f"/v1/statements/{statement_id}")
    assert response.status_code == 200

    response = client.post(
        "/v1/statements",
        json={"sympy": "K - 1/2*m*v**2", "latex": r"K = \frac{1}{2} m v^2"},
    )
    assert response.status_code == 200


def test_derivation_and_path() -> None:
    setup_module()
    client = TestClient(api_main.app)

    s1 = client.post("/v1/statements", json={"sympy": "F - m*a"}).json()["id"]
    s2 = client.post("/v1/statements", json={"sympy": "m*a - F"}).json()["id"]

    response = client.post(
        "/v1/derivations",
        json={
            "inputs": [s1],
            "outputs": [s2],
            "rule_tags": ["algebra"],
            "exact": True,
            "assumptions": [],
        },
    )
    assert response.status_code == 200
    derivation_id = response.json()["id"]

    response = client.get(f"/v1/derivations/{derivation_id}")
    assert response.status_code == 200

    response = client.get(f"/v1/paths?src={s1}&dst={s2}&preferences=algebra")
    assert response.status_code == 200
    payload = response.json()
    assert s1 in payload["path"] and s2 in payload["path"]
