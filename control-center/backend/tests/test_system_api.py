"""Pruebas de la API de información del sistema."""

from fastapi.testclient import TestClient

from app.adapters.base.system_adapter import SystemAdapter
from app.api.dependencies import get_system_service
from app.main import app
from app.services.system_service import SystemService
from app.domain.system import (
    CPUInfo,
    DiskInfo,
    MemoryInfo,
    UptimeInfo,
)

class FakeSystemAdapter(SystemAdapter):
    """Adaptador determinista para pruebas de API."""

    def hostname(self) -> str:
        return "ejtv-api-test"

    def operating_system(self) -> str:
        return "API Test Linux 1.0"

    def kernel(self) -> str:
        return "1.0.0-api-test"

    def cpu_info(self) -> CPUInfo:
        return CPUInfo(
            usage_percent=25.0,
            logical_cores=8,
            physical_cores=4,
            frequency_mhz=2800.0,
        )

    def memory_info(self) -> MemoryInfo:
        return MemoryInfo(
            total_bytes=8_000,
            available_bytes=5_000,
            used_bytes=3_000,
            usage_percent=37.5,
        )

    def disk_info(self) -> DiskInfo:
        return DiskInfo(
            total_bytes=100_000,
            used_bytes=40_000,
            free_bytes=60_000,
            usage_percent=40.0,
        )

    def uptime_info(self) -> UptimeInfo:
        return UptimeInfo(
            uptime_seconds=86_400,
        )


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

def test_system_resources_endpoint() -> None:
    response = client.get("/api/v1/system/resources")

    assert response.status_code == 200

    payload = response.json()

    assert payload["success"] is True
    assert payload["data"]["cpu"] == {
        "usage_percent": 25.0,
        "logical_cores": 8,
        "physical_cores": 4,
        "frequency_mhz": 2800.0,
    }
    assert payload["data"]["memory"] == {
        "total_bytes": 8_000,
        "available_bytes": 5_000,
        "used_bytes": 3_000,
        "usage_percent": 37.5,
    }
    assert payload["data"]["disk"] == {
        "total_bytes": 100_000,
        "used_bytes": 40_000,
        "free_bytes": 60_000,
        "usage_percent": 40.0,
    }
    assert payload["data"]["uptime"] == {
        "uptime_seconds": 86_400,
    }
    assert payload["data"]["captured_at"]
    assert payload["message"] == (
        "Recursos del sistema obtenidos correctamente."
    )
    assert payload["request_id"]