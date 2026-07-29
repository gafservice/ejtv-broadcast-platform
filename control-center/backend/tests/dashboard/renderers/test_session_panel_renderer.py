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
        protocol_counts=(
            ("SRT", 7),
            ("RTMP", 2),
            ("RTSP", 1),
            ("HLS", 1),
            ("WebRTC", 1),
            ("UNKNOWN", 0),
        ),
    )


def test_render_returns_panel() -> None:
    panel = SessionPanelRenderer().render(
        build_panel()
    )

    assert isinstance(panel, Panel)
    assert panel.title == "ACTIVE CLIENTS"


def test_render_contains_protocol_counts() -> None:
    panel = SessionPanelRenderer().render(
        build_panel()
    )

    text = str(panel.renderable)

    assert "SRT: 7" in text
    assert "RTMP: 2" in text
    assert "RTSP: 1" in text
    assert "HLS: 1" in text
    assert "WebRTC: 1" in text


def test_render_contains_total_and_operational_values() -> None:
    panel = SessionPanelRenderer().render(
        build_panel()
    )

    text = str(panel.renderable)

    assert "TOTAL: 12" in text
    assert "Total traffic: 42.00 Mbps" in text
    assert "Avg/client: 3.50 Mbps" in text

    assert "Inbound" not in text
    assert "Outbound" not in text
    assert "8.00 Mbps" not in text

    assert "GOOD" not in text
    assert "Quality" not in text


def test_render_omits_unknown_protocol() -> None:
    panel = SessionPanelRenderer().render(
        build_panel()
    )

    text = str(panel.renderable)

    assert "UNKNOWN" not in text


def test_render_omits_legacy_role_counters() -> None:
    panel = SessionPanelRenderer().render(
        build_panel()
    )

    text = str(panel.renderable)

    assert "Readers" not in text
    assert "Publishers" not in text
    assert "Degraded" not in text
    assert "Critical" not in text


def test_format_none_bitrate() -> None:
    assert (
        SessionPanelRenderer._format_bitrate(None)
        == "N/A"
    )


def test_format_valid_bitrate() -> None:
    assert (
        SessionPanelRenderer._format_bitrate(
            12_500_000
        )
        == "12.50 Mbps"
    )