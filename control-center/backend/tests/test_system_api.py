"""Pruebas de la API de información del sistema."""

from fastapi.testclient import TestClient

from app.adapters.base.system_adapter import SystemAdapter
from app.api.dependencies import get_system_service
from app.main import app
from app.services.system_service import SystemService


class FakeSystemAdapter(SystemAdapter):
    """Adaptador determinista para pruebas de API."""

    def hostname(self) -> str:
        return "ejtv-api-test"

    def operating_system(self) -> str:
        return "API Test Linux 1.0"

    def kernel(self) -> str:
        return "1.0.0-api-test"


def override_system_service() -> SystemService:
    return SystemService(FakeSystemAdapter())


app.dependency_overrides[get_system_service] = override_system_service

client = TestClient(app)


def test_system_info_endpoint() -> None:
    response = client.get("/api/v1/system/info")

    assert response.status_code == 200

    payload = response.json()

    assert payload["success"] is True
    assert payload["data"] == {
        "hostname": "ejtv-api-test",
        "operating_system": "API Test Linux 1.0",
        "kernel": "1.0.0-api-test",
    }
    assert payload["message"] == (
        "Información del sistema obtenida correctamente."
    )
    assert payload["request_id"]


def test_system_info_preserves_request_id() -> None:
    request_id = "system-api-test"

    response = client.get(
        "/api/v1/system/info",
        headers={"X-Request-ID": request_id},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_id
    assert response.json()["request_id"] == request_id
