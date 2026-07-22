"""Pruebas básicas del núcleo del Backend."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_endpoint() -> None:
    response = client.get("/")

    assert response.status_code == 200

    payload = response.json()

    assert payload["success"] is True
    assert payload["data"]["application"] == "Control Center"
    assert payload["data"]["status"] == "running"
    assert payload["request_id"]


def test_health_endpoint() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200

    payload = response.json()

    assert payload["success"] is True
    assert payload["data"]["status"] == "healthy"
    assert payload["data"]["api_version"] == "v1"
    assert payload["request_id"]


def test_unknown_route_uses_standard_error() -> None:
    response = client.get("/api/v1/nonexistent")

    assert response.status_code == 404

    payload = response.json()

    assert payload["success"] is False
    assert payload["error"]["code"] == "HTTP_404"
    assert payload["request_id"]


def test_request_id_is_preserved() -> None:
    request_id = "sprint-1-test"

    response = client.get(
        "/api/v1/health",
        headers={"X-Request-ID": request_id},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_id
    assert response.json()["request_id"] == request_id
