"""Pruebas del servicio de información del sistema."""
from datetime import UTC, datetime
from app.adapters.base.system_adapter import SystemAdapter
from app.domain.system import (
    CPUInfo,
    DiskInfo,
    MemoryInfo,
    SystemInfo,
    SystemResources,
    UptimeInfo,
    MonitoredService,
    ServiceMonitoringSnapshot,
    ServiceStatus,
)
from app.services.system_service import SystemService

class FakeSystemAdapter(SystemAdapter):
    """Adaptador controlado utilizado exclusivamente en pruebas."""

    def hostname(self) -> str:
        return "ejtv-test"

    def operating_system(self) -> str:
        return "Test Linux 1.0"

    def kernel(self) -> str:
        return "1.0.0-test"

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


def test_system_service_returns_system_info() -> None:
    service = SystemService(FakeSystemAdapter())

    result = service.get_system_info()

    assert isinstance(result, SystemInfo)
    assert result.hostname == "ejtv-test"
    assert result.operating_system == "Test Linux 1.0"
    assert result.kernel == "1.0.0-test"




def test_system_service_uses_adapter_contract() -> None:
    adapter: SystemAdapter = FakeSystemAdapter()
    service = SystemService(adapter)

    assert service.get_system_info() == SystemInfo(
        hostname="ejtv-test",
        operating_system="Test Linux 1.0",
        kernel="1.0.0-test",
    )

def test_system_service_returns_system_resources() -> None:
    service = SystemService(FakeSystemAdapter())

    result = service.get_system_resources()

    assert isinstance(result, SystemResources)
    assert result.cpu.usage_percent == 25.0
    assert result.cpu.logical_cores == 8
    assert result.memory.used_bytes == 3_000
    assert result.disk.free_bytes == 60_000
    assert result.uptime.uptime_seconds == 86_400
    assert result.captured_at.tzinfo is not None

def test_system_service_returns_service_monitoring() -> None:
    service = SystemService(FakeSystemAdapter())

    result = service.get_service_monitoring()

    assert isinstance(result, ServiceMonitoringSnapshot)
    assert len(result.services) == 2
    assert result.services[0].name == "MediaMTX"
    assert result.services[0].status is ServiceStatus.RUNNING
    assert result.services[1].name == "FFmpeg"
    assert result.services[1].status is ServiceStatus.STOPPED
    assert result.captured_at.tzinfo is not None