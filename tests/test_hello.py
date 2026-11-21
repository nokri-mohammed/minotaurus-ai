from fastapi.testclient import TestClient

from minotaurus.server.app import app


def test_hello_endpoint() -> None:
    response = TestClient(app).get("/api/hello")
    assert response.status_code == 200
    assert response.json()["engine"] == "engine ready"
