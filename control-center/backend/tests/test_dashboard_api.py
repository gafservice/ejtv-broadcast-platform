"""Pruebas HTTP del endpoint Dashboard."""

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_dashboard_endpoint_requires_authentication() -> None:
    response = client.get("/api/v1/dashboard")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"

    body = response.json()

    assert body["success"] is False
    assert body["error"]["code"] == "HTTP_401"
    assert body["message"] == (
        "Se requiere un token de acceso válido."
    )
