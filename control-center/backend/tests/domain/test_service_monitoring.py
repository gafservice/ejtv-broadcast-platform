"""Pruebas del dominio de monitoreo de servicios."""

from datetime import UTC, datetime

import pytest

from app.domain.system import (
    MonitoredService,
    ServiceInstance,
    ServiceMonitoringSnapshot,
    ServiceStatus,
)


def test_service_instance_creation() -> None:
    instance = ServiceInstance(
        pid=1234,
        cpu_percent=12.5,
        memory_bytes=50_000_000,
        uptime_seconds=3600,
    )

    assert instance.pid == 1234
    assert instance.cpu_percent == 12.5
    assert instance.memory_bytes == 50_000_000
    assert instance.uptime_seconds == 3600


def test_service_instance_rejects_invalid_pid() -> None:
    with pytest.raises(ValueError):
        ServiceInstance(
            pid=0,
            cpu_percent=0.0,
            memory_bytes=0,
            uptime_seconds=0,
        )


def test_monitored_service_running() -> None:
    service = MonitoredService(
        name="MediaMTX",
        identifier="mediamtx.service",
        monitor_type="systemd",
        status=ServiceStatus.RUNNING,
        instances=(
            ServiceInstance(
                pid=3928030,
                cpu_percent=1.2,
                memory_bytes=60_000_000,
                uptime_seconds=86_400,
            ),
        ),
    )

    assert service.name == "MediaMTX"
    assert service.status is ServiceStatus.RUNNING
    assert len(service.instances) == 1


def test_monitored_service_can_be_stopped_without_instances() -> None:
    service = MonitoredService(
        name="FFmpeg",
        identifier="ffmpeg",
        monitor_type="process",
        status=ServiceStatus.STOPPED,
        instances=(),
    )

    assert service.status is ServiceStatus.STOPPED
    assert service.instances == ()


def test_monitoring_snapshot_creation() -> None:
    snapshot = ServiceMonitoringSnapshot(
        services=(
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

    assert len(snapshot.services) == 1
    assert snapshot.captured_at.tzinfo is not None


def test_monitoring_snapshot_requires_timezone() -> None:
    with pytest.raises(ValueError):
        ServiceMonitoringSnapshot(
            services=(),
            captured_at=datetime.now(),
        )