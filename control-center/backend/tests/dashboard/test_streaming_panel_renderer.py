"""Pruebas del renderizador del panel STREAMING."""

from rich.console import Console
from rich.panel import Panel

from app.dashboard.models import StreamingPanelData
from app.dashboard.renderers.streaming_panel_renderer import (
    StreamingPanelRenderer,
)


def test_streaming_panel_renderer_can_be_created() -> None:
    renderer = StreamingPanelRenderer()

    assert renderer is not None


def test_render_returns_rich_panel() -> None:
    renderer = StreamingPanelRenderer()

    data = StreamingPanelData(
        active_paths=3,
        readers=12,
        inbound_bitrate_bps=8_000_000,
        outbound_bitrate_bps=24_000_000,
        quality="AVAILABLE",
    )

    panel = renderer.render(data)

    assert isinstance(panel, Panel)


def test_render_contains_streaming_values() -> None:
    renderer = StreamingPanelRenderer()

 
    data = StreamingPanelData(
        active_paths=3,
        readers=12,
        inbound_bitrate_bps=8_000_000,
        outbound_bitrate_bps=24_000_000,
        quality="AVAILABLE",
    )



    panel = renderer.render(data)

    console = Console(record=True, width=120)
    console.print(panel)

    output = console.export_text()

    assert "Paths" in output
    assert "3" in output
    assert "Readers" in output
    assert "12" in output
    assert "Inbound" in output
    assert "8.00 Mbps" in output
    assert "Outbound" in output
    assert "24.00 Mbps" in output
    assert "Quality" in output
    assert "AVAILABLE" in output
