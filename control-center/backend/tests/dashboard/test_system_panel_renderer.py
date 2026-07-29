"""Pruebas del renderizador del panel SYSTEM."""

from datetime import datetime, timezone

from rich.console import Console

from app.dashboard.models import (
    CpuPanelData,
    DiskPanelData,
    MemoryPanelData,
    NetworkPanelData,
    SystemPanelData,
    UptimePanelData,
)
from app.dashboard.renderers.system_panel_renderer import (
    SystemPanelRenderer,
)


def _render_to_text(data: SystemPanelData) -> str:
    """Renderiza el panel en una consola de texto para inspección."""

    console = Console(
        record=True,
        width=100,
        color_system=None,
    )

    console.print(
        SystemPanelRenderer().render(data)
    )

    return console.export_text()


def _build_system_panel_data(
    *,
    rx_bps: float | None,
    tx_bps: float | None,
) -> SystemPanelData:
    """Construye datos válidos para las pruebas del renderer."""

    return SystemPanelData(
        cpu=CpuPanelData(
            usage_percent=25.0,
            per_core_usage_percent=(20.0, 30.0),
            logical_cores=2,
            physical_cores=1,
            frequency_mhz=3000.0,
        ),
        memory=MemoryPanelData(
            usage_percent=50.0,
            used_bytes=4 * 1024**3,
            total_bytes=8 * 1024**3,
        ),
        disk=DiskPanelData(
            usage_percent=40.0,
            used_bytes=200 * 1024**3,
            total_bytes=500 * 1024**3,
        ),
        network=NetworkPanelData(
            interface="ens2f0",
            rx_bps=rx_bps,
            tx_bps=tx_bps,
            errors_in=1,
            errors_out=2,
            dropped_in=3,
            dropped_out=4,
        ),
        uptime=UptimePanelData(
            seconds=90_061,
        ),
        captured_at=datetime(
            2026,
            7,
            24,
            12,
            0,
            tzinfo=timezone.utc,
        ),
    )


def test_system_panel_renderer_shows_unavailable_network_rates() -> None:
    """La primera captura debe mostrar tasas no disponibles."""

    data = _build_system_panel_data(
        rx_bps=None,
        tx_bps=None,
    )

    output = _render_to_text(data)

    assert "Red: ens2f0" in output
    assert "RX: N/D | TX: N/D" in output


def test_system_panel_renderer_formats_network_rates() -> None:
    """Las tasas disponibles deben mostrarse en unidades legibles."""

    data = _build_system_panel_data(
        rx_bps=8_000_000,
        tx_bps=4_000_000,
    )

    output = _render_to_text(data)

    assert "RX: 8.00 Mbps | TX: 4.00 Mbps" in output
    assert "Errores RX/TX: 1 / 2" in output
    assert "Descartes RX/TX: 3 / 4" in output
