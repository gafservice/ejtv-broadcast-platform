"""Pruebas de la especificación OpenAPI."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_openapi_document_is_available() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200

    document = response.json()

    assert document["info"]["title"] == "Control Center"
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


def test_bearer_security_scheme_is_registered() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200

    document = response.json()

    scheme = document["components"]["securitySchemes"][
        "BearerAuth"
    ]

    assert scheme["type"] == "http"
    assert scheme["scheme"] == "bearer"


def test_auth_me_is_protected_by_bearer_auth() -> None:
    response = client.get("/openapi.json")

    operation = response.json()["paths"][
        "/api/v1/auth/me"
    ]["get"]

    assert operation["security"] == [
        {
            "BearerAuth": [],
        }
    ]


def test_dashboard_is_protected_by_bearer_auth() -> None:
    response = client.get("/openapi.json")

    operation = response.json()["paths"][
        "/api/v1/dashboard"
    ]["get"]

    assert operation["security"] == [
        {
            "BearerAuth": [],
        }
    ]


def test_system_routes_are_protected_by_bearer_auth() -> None:
    response = client.get("/openapi.json")

    paths = response.json()["paths"]

    for path in (
        "/api/v1/system/info",
        "/api/v1/system/resources",
        "/api/v1/system/services",
    ):
        assert paths[path]["get"]["security"] == [
            {
                "BearerAuth": [],
            }
        ]


def test_login_remains_public_in_openapi() -> None:
    response = client.get("/openapi.json")

    operation = response.json()["paths"][
        "/api/v1/auth/login"
    ]["post"]

    assert "security" not in operation


def test_health_remains_public_in_openapi() -> None:
    response = client.get("/openapi.json")

    operation = response.json()["paths"][
        "/api/v1/health"
    ]["get"]

    assert "security" not in operation
