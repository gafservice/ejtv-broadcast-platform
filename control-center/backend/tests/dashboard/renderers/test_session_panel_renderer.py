"""Pruebas del renderizador ACTIVE CLIENTS."""

from rich.panel import Panel

from app.dashboard.models import SessionPanelData
from app.dashboard.renderers.session_panel_renderer import (
    SessionPanelRenderer,
)


def build_panel() -> SessionPanelData:
    return SessionPanelData(
        total_sessions=12,
        readers=10,
        publishers=2,
        degraded_sessions=3,
        critical_sessions=1,
        inbound_bitrate_bps=8_000_000,
        outbound_bitrate_bps=42_000_000,
        quality="GOOD",
    )


def test_render_returns_panel():
    panel = SessionPanelRenderer().render(
        build_panel()
    )

    assert isinstance(panel, Panel)
    assert panel.title == "ACTIVE CLIENTS"


def test_render_contains_values():
    panel = SessionPanelRenderer().render(
        build_panel()
    )

    text = str(panel.renderable)

    assert "12" in text
    assert "10" in text
    assert "2" in text
    assert "GOOD" in text
    assert "8.00 Mbps" in text
    assert "42.00 Mbps" in text


def test_format_none_bitrate():
    assert (
        SessionPanelRenderer._format_bitrate(None)
        == "N/A"
    )


def test_format_valid_bitrate():
    assert (
        SessionPanelRenderer._format_bitrate(
            12_500_000
        )
        == "12.50 Mbps"
    )
