"""Contracts for IncomingPanelRenderer."""

from rich.console import Console

from app.dashboard.models.incoming_panel import (
    IncomingPanelData,
    IncomingRowData,
)
from app.dashboard.renderers.incoming_panel_renderer import (
    IncomingPanelRenderer,
)
from app.domain.streaming.health import HealthStatus


def _render_text(data: IncomingPanelData | None) -> str:
    panel = IncomingPanelRenderer().render(data)
    console = Console(
        record=True,
        width=180,
        color_system=None,
    )
    console.print(panel)
    return console.export_text()


def test_render_projects_incoming_rows() -> None:
    data = IncomingPanelData(
        rows=(
            IncomingRowData(
                path_name="alpha-feed",
                source="SRT",
                status="READY",
                bitrate_receive_mbps=5.25,
                health_status=HealthStatus.HEALTHY,
                protocol="SRT",
                remote_address="203.0.113.10:9000",
            ),
            IncomingRowData(
                path_name="beta-feed",
                source="MPEG-TS",
                status="READY",
                bitrate_receive_mbps=3.75,
                health_status=None,
            ),
        ),
    )

    output = _render_text(data)

    assert "INCOMING SIGNALS" in output
    assert "alpha-feed" in output
    assert "beta-feed" in output
    assert "SRT" in output
    assert "MPEG-TS" in output
    assert "203.0.113.10:9000" in output
    assert "5.25 Mbps" in output
    assert "3.75 Mbps" in output
    assert "READY" in output
    assert "HEALTHY" in output
    assert "N/A" in output


def test_render_none_reports_unavailable_data() -> None:
    output = _render_text(None)

    assert "INCOMING SIGNALS" in output
    assert "Incoming data unavailable." in output


def test_render_empty_reports_no_incoming_signals() -> None:
    output = _render_text(IncomingPanelData())

    assert "INCOMING SIGNALS" in output
    assert "No incoming signals." in output
