"""Pruebas del renderizador del panel SERVER."""

from datetime import datetime, timezone

from rich.panel import Panel

from app.dashboard.models import ServerPanelData
from app.dashboard.renderers.server_panel_renderer import (
    ServerPanelRenderer,
)


def test_server_panel_renderer_can_be_created() -> None:
    renderer = ServerPanelRenderer()

    assert renderer is not None


def test_render_returns_rich_panel() -> None:
    renderer = ServerPanelRenderer()

    data = ServerPanelData(
        hostname="server-01",
        mediamtx_online=True,
        api_online=True,
        snapshot_at=datetime(
            2026,
            7,
            20,
            20,
            30,
            tzinfo=timezone.utc,
        ),
        quality="AVAILABLE",
    )

    result = renderer.render(data)

    assert isinstance(result, Panel)

from rich.console import Console


def test_render_contains_hostname() -> None:
    renderer = ServerPanelRenderer()

    data = ServerPanelData(
        hostname="server-01",
        mediamtx_online=True,
        api_online=True,
        snapshot_at=datetime(
            2026,
            7,
            20,
            20,
            30,
            tzinfo=timezone.utc,
        ),
        quality="AVAILABLE",
    )

    panel = renderer.render(data)

    console = Console(record=True, width=120)
    console.print(panel)

    output = console.export_text()

    assert "server-01" in output

from rich.console import Console


def test_render_contains_hostname() -> None:
    renderer = ServerPanelRenderer()

    data = ServerPanelData(
        hostname="server-01",
        mediamtx_online=True,
        api_online=True,
        snapshot_at=datetime(
            2026,
            7,
            20,
            20,
            30,
            tzinfo=timezone.utc,
        ),
        quality="AVAILABLE",
    )

    panel = renderer.render(data)

    console = Console(record=True, width=120)
    console.print(panel)

    output = console.export_text()

    assert "server-01" in output

def test_render_contains_server_labels() -> None:
    renderer = ServerPanelRenderer()

    data = ServerPanelData(
        hostname="server-01",
        mediamtx_online=True,
        api_online=False,
        snapshot_at=datetime(
            2026,
            7,
            20,
            20,
            30,
            tzinfo=timezone.utc,
        ),
        quality="AVAILABLE",
    )

    panel = renderer.render(data)

    console = Console(record=True, width=120)
    console.print(panel)

    output = console.export_text()

    assert "Hostname" in output
    assert "MediaMTX" in output
    assert "API" in output
    assert "Snapshot" in output
    assert "Quality" not in output

def test_render_formats_service_statuses() -> None:
    renderer = ServerPanelRenderer()

    data = ServerPanelData(
        hostname="server-01",
        mediamtx_online=True,
        api_online=False,
        snapshot_at=datetime(
            2026,
            7,
            20,
            20,
            30,
            tzinfo=timezone.utc,
        ),
        quality="AVAILABLE",
    )

    panel = renderer.render(data)

    console = Console(record=True, width=120)
    console.print(panel)

    output = console.export_text()

    assert "MediaMTX: ONLINE" in output
    assert "API: OFFLINE" in output

def test_render_formats_snapshot_timestamp() -> None:
    renderer = ServerPanelRenderer()

    data = ServerPanelData(
        hostname="server-01",
        mediamtx_online=True,
        api_online=True,
        snapshot_at=datetime(
            2026,
            7,
            20,
            20,
            30,
            45,
            tzinfo=timezone.utc,
        ),
        quality="AVAILABLE",
    )

    panel = renderer.render(data)

    console = Console(record=True, width=120)
    console.print(panel)

    output = console.export_text()

    assert "2026-07-20T20:30:45+00:00" in output