"""Pruebas para DashboardRenderer."""
from rich.console import Console

from app.domain.streaming import HealthStatus, StreamingHealth

from datetime import datetime, timezone

from rich.layout import Layout

from app.dashboard.models import (
    DashboardData,
    PathRowData,
    ServerPanelData,
    StreamingPanelData,
)
from app.dashboard.renderers.dashboard_renderer import DashboardRenderer


def build_dashboard_data() -> DashboardData:
    """Construye datos válidos para las pruebas del renderer."""

    return DashboardData(
        server=ServerPanelData(
            hostname="ejtv-01",
            mediamtx_online=True,
            api_online=True,
            snapshot_at=datetime(
                2026,
                7,
                21,
                14,
                0,
                tzinfo=timezone.utc,
            ),
            quality="AVAILABLE",
        ),
        streaming=StreamingPanelData(
            active_paths=1,
            readers=5,
            inbound_bitrate_bps=8_000_000,
            outbound_bitrate_bps=40_000_000,
            quality="AVAILABLE",
        ),
        paths=(
            PathRowData(
                name="enlace",
                source="UDP",
                readers=5,
                inbound_bitrate_bps=8_000_000,
                outbound_bitrate_bps=40_000_000,
                status="ACTIVE",
                quality="AVAILABLE",
            ),
        ),
        health=None,
    )


def test_dashboard_renderer_can_be_created() -> None:
    renderer = DashboardRenderer()

    assert renderer is not None


def test_render_returns_rich_layout() -> None:
    renderer = DashboardRenderer()
    data = build_dashboard_data()

    layout = renderer.render(data)

    assert isinstance(layout, Layout)
def test_render_contains_health_panel() -> None:
    renderer = DashboardRenderer()
    data = build_dashboard_data()

    layout = renderer.render(data)

    console = Console(
        record=True,
        width=160,
        color_system=None,
    )
    console.print(layout)

    output = console.export_text()

    assert "STREAM HEALTH" in output
    assert "UNKNOWN" in output
    assert "No health data available." in output


def test_render_contains_streaming_health_data() -> None:
    renderer = DashboardRenderer()
    data = build_dashboard_data()

    health = StreamingHealth(
        captured_at=data.server.snapshot_at,
        paths=(),
        status=HealthStatus.HEALTHY,
        message="El subsistema SRT funciona correctamente.",
    )

    data = DashboardData(
        server=data.server,
        streaming=data.streaming,
        paths=data.paths,
        health=health,
    )

    layout = renderer.render(data)

    console = Console(
        record=True,
        width=160,
        color_system=None,
    )
    console.print(layout)

    output = console.export_text()

    assert "STREAM HEALTH" in output
    assert "HEALTHY" in output
    assert "Summary" in output
    assert "El subsistema SRT funciona" in output
    assert "…" in output
