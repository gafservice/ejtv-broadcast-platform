"""Pruebas de la especificación OpenAPI."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_openapi_document_is_available() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200

    document = response.json()

    assert document["info"]["title"] == "EJTV Control Center"
    assert document["info"]["version"] == "0.2.0"


def test_required_paths_are_registered() -> None:
    response = client.get("/openapi.json")

    paths = response.json()["paths"]

    assert "/" in paths
    assert "/api/v1/health" in paths
    assert "/api/v1/system/info" in paths


def test_system_endpoint_is_grouped_under_system_tag() -> None:
    response = client.get("/openapi.json")

    operation = response.json()["paths"]["/api/v1/system/info"]["get"]

    assert "System" in operation["tags"]
