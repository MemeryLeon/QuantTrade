from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_smoke() -> None:
    client = TestClient(app)

    response = client.get("/health", headers={"X-Trace-ID": "trace-test"})

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Trace-ID"] == "trace-test"
