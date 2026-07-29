"""Pruebas de los modelos especializados del panel SYSTEM."""

from datetime import UTC, datetime

import pytest

from app.dashboard.models import (
    CpuPanelData,
    DiskPanelData,
    MemoryPanelData,
    NetworkPanelData,
    SystemPanelData,
    UptimePanelData,
)


def build_system_panel_data() -> SystemPanelData:
    """Construye datos válidos para el panel SYSTEM."""

    return SystemPanelData(
        cpu=CpuPanelData(
            usage_percent=25.0,
            per_core_usage_percent=(20.0, 30.0),
            logical_cores=8,
            physical_cores=4,
            frequency_mhz=2800.0,
        ),
        memory=MemoryPanelData(
            usage_percent=37.5,
            used_bytes=3_000,
            total_bytes=8_000,
        ),
        disk=DiskPanelData(
            usage_percent=40.0,
            used_bytes=40_000,
            total_bytes=100_000,
        ),
        network=NetworkPanelData(
            interface="ens2f0",
            rx_bps=None,
            tx_bps=None,
            errors_in=0,
            errors_out=0,
            dropped_in=0,
            dropped_out=0,
        ),
        uptime=UptimePanelData(
            seconds=86_400.0,
        ),
        captured_at=datetime(
            2026,
            7,
            24,
            12,
            0,
            tzinfo=UTC,
        ),
    )


def test_system_panel_groups_specialized_models() -> None:
    """SYSTEM debe agrupar cada familia de métricas."""

    data = build_system_panel_data()

    assert data.cpu.usage_percent == 25.0
    assert data.memory.used_bytes == 3_000
    assert data.disk.total_bytes == 100_000
    assert data.network.interface == "ens2f0"
    assert data.uptime.seconds == 86_400.0


def test_cpu_rejects_invalid_usage_percent() -> None:
    """CPU debe rechazar porcentajes fuera del rango válido."""

    with pytest.raises(ValueError):
        CpuPanelData(
            usage_percent=101.0,
            per_core_usage_percent=(),
            logical_cores=8,
            physical_cores=4,
            frequency_mhz=2800.0,
        )


def test_cpu_rejects_invalid_per_core_usage() -> None:
    """CPU debe validar cada núcleo individual."""

    with pytest.raises(ValueError):
        CpuPanelData(
            usage_percent=20.0,
            per_core_usage_percent=(10.0, -1.0),
            logical_cores=8,
            physical_cores=4,
            frequency_mhz=2800.0,
        )


def test_memory_rejects_used_bytes_above_total() -> None:
    """Memoria utilizada no debe superar la memoria total."""

    with pytest.raises(ValueError):
        MemoryPanelData(
            usage_percent=50.0,
            used_bytes=9_000,
            total_bytes=8_000,
        )


def test_disk_rejects_used_bytes_above_total() -> None:
    """Espacio utilizado no debe superar el espacio total."""

    with pytest.raises(ValueError):
        DiskPanelData(
            usage_percent=50.0,
            used_bytes=110_000,
            total_bytes=100_000,
        )


def test_network_accepts_unavailable_rates() -> None:
    """La primera captura puede no contener tasas RX/TX."""

    data = NetworkPanelData(
        interface=" ens2f0 ",
        rx_bps=None,
        tx_bps=None,
        errors_in=0,
        errors_out=0,
        dropped_in=0,
        dropped_out=0,
    )

    assert data.interface == "ens2f0"
    assert data.rx_bps is None
    assert data.tx_bps is None


def test_network_rejects_negative_rate() -> None:
    """Una tasa de red no puede ser negativa."""

    with pytest.raises(ValueError):
        NetworkPanelData(
            interface="ens2f0",
            rx_bps=-1.0,
            tx_bps=0.0,
            errors_in=0,
            errors_out=0,
            dropped_in=0,
            dropped_out=0,
        )


def test_uptime_rejects_negative_seconds() -> None:
    """El uptime no puede ser negativo."""

    with pytest.raises(ValueError):
        UptimePanelData(seconds=-1.0)


def test_system_panel_rejects_naive_timestamp() -> None:
    """La captura debe incluir zona horaria."""

    valid = build_system_panel_data()

    with pytest.raises(ValueError):
        SystemPanelData(
            cpu=valid.cpu,
            memory=valid.memory,
            disk=valid.disk,
            network=valid.network,
            uptime=valid.uptime,
            captured_at=datetime(2026, 7, 24, 12, 0),
        )
