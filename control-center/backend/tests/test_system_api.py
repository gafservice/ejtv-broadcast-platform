"""Pruebas de la API de información del sistema."""

import pytest
from fastapi.testclient import TestClient
from datetime import UTC, datetime
from uuid import UUID
from app.adapters.base.system_adapter import SystemAdapter
from app.api.dependencies import get_system_service
from app.api.security import get_current_identity
from app.domain.identity.entities import AuthenticatedIdentity
from app.domain.identity.value_objects import (
    PermissionName,
    RoleName,
    UserId,
    Username,
)
from app.main import app
from app.services.system_service import SystemService
from app.domain.system import (
    CPUInfo,
    DiskInfo,
    MemoryInfo,
    NetworkInfo,
    NetworkInterfaceInfo,
    NetworkInterfaceType,
    UptimeInfo,
    MonitoredService,
    ServiceMonitoringSnapshot,
    ServiceStatus,
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

    def network_info(self, interface: str) -> NetworkInfo:
        return NetworkInfo(
            interface=interface,
            bytes_sent=1_000_000,
            bytes_received=2_000_000,
            packets_sent=10_000,
            packets_received=20_000,
            errors_in=0,
            errors_out=0,
            dropped_in=0,
            dropped_out=0,
        )


    def network_interfaces(self) -> tuple[NetworkInfo, ...]:
        """Retorna las interfaces disponibles del adapter falso."""

        return (
            self.network_info("ens2f0"),
        )

    def network_interface_infos(
        self,
    ) -> tuple[NetworkInterfaceInfo, ...]:
        """Retorna identidad y estado de las interfaces."""

        return (
            NetworkInterfaceInfo(
                interface="ens2f0",
                interface_type=NetworkInterfaceType.ETHERNET,
                is_up=True,
                carrier=True,
                mtu=1500,
                link_speed_mbps=100,
            ),
        )

    def uptime_info(self) -> UptimeInfo:
        return UptimeInfo(
            uptime_seconds=86_400,
        )

    def service_monitoring(
        self,
    ) -> ServiceMonitoringSnapshot:
        return ServiceMonitoringSnapshot(
            services=(
                MonitoredService(
                    name="MediaMTX",
                    identifier="mediamtx.service",
                    monitor_type="systemd",
                    status=ServiceStatus.RUNNING,
                    instances=(),
                ),
                MonitoredService(
                    name="FFmpeg",
                    identifier="ffmpeg",
                    monitor_type="process",
                    status=ServiceStatus.STOPPED,
                    instances=(),
                ),
            ),
            captured_at=datetime.now(UTC),
        )


def override_system_service() -> SystemService:
    return SystemService(FakeSystemAdapter())


def override_current_identity() -> AuthenticatedIdentity:
    """Retorna una identidad autorizada para consultar System."""

    return AuthenticatedIdentity(
        user_id=UserId(
            UUID("01900000-0000-7000-8000-000000000012")
        ),
        username=Username("systemtester"),
        roles=frozenset(
            {
                RoleName("administrator"),
            }
        ),
        permissions=frozenset(
            {
                PermissionName("system.read"),
            }
        ),
    )


@pytest.fixture
def client() -> TestClient:
    """Proporciona un cliente con dependencias aisladas."""

    previous_system_service = app.dependency_overrides.get(
        get_system_service
    )
    previous_identity = app.dependency_overrides.get(
        get_current_identity
    )

    app.dependency_overrides[get_system_service] = (
        override_system_service
    )
    app.dependency_overrides[get_current_identity] = (
        override_current_identity
    )

    with TestClient(app) as test_client:
        yield test_client

    if previous_system_service is None:
        app.dependency_overrides.pop(
            get_system_service,
            None,
        )
    else:
        app.dependency_overrides[
            get_system_service
        ] = previous_system_service

    if previous_identity is None:
        app.dependency_overrides.pop(
            get_current_identity,
            None,
        )
    else:
        app.dependency_overrides[
            get_current_identity
        ] = previous_identity


def test_system_info_endpoint(
    client: TestClient,
) -> None:
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


def test_system_info_preserves_request_id(
    client: TestClient,
) -> None:
    request_id = "system-api-test"

    response = client.get(
        "/api/v1/system/info",
        headers={"X-Request-ID": request_id},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_id
    assert response.json()["request_id"] == request_id

def test_system_resources_endpoint(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/system/resources")

    assert response.status_code == 200

    payload = response.json()

    assert payload["success"] is True

    assert payload["data"]["cpu"] == {
        "usage_percent": 25.0,
        "logical_cores": 8,
        "physical_cores": 4,
        "frequency_mhz": 2800.0,
        "per_core_usage_percent": [],
    }

    assert payload["data"]["memory"] == {
        "total_bytes": 8_000,
        "available_bytes": 5_000,
        "used_bytes": 3_000,
        "usage_percent": 37.5,
        "free_bytes": 0,
        "cached_bytes": 0,
        "buffers_bytes": 0,
    }

    assert payload["data"]["disk"] == {
    "total_bytes": 100_000,
    "used_bytes": 40_000,
    "free_bytes": 60_000,
    "usage_percent": 40.0,
    "device": "unknown",
    "mount_point": "/",
    "filesystem_type": "unknown",
    }

    assert payload["data"]["uptime"] == {
        "uptime_seconds": 86_400,
    }

    assert payload["data"]["captured_at"]
    assert payload["message"] == (
        "Recursos del sistema obtenidos correctamente."
    )
    assert payload["request_id"]
    
def test_system_services_endpoint(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/system/services")

    assert response.status_code == 200

    payload = response.json()

    assert payload["success"] is True
    assert len(payload["data"]["services"]) == 2

    assert payload["data"]["services"][0] == {
        "name": "MediaMTX",
        "identifier": "mediamtx.service",
        "monitor_type": "systemd",
        "status": "running",
        "instances": [],
    }

    assert payload["data"]["services"][1] == {
        "name": "FFmpeg",
        "identifier": "ffmpeg",
        "monitor_type": "process",
        "status": "stopped",
        "instances": [],
    }

    assert payload["data"]["captured_at"]
    assert payload["message"] == (
        "Servicios monitoreados obtenidos correctamente."
    )
    assert payload["request_id"]   
