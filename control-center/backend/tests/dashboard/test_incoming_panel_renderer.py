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


def test_renderer_presents_health_reason_without_interpretation() -> None:
    data = IncomingPanelData(
        rows=(
            IncomingRowData(
                path_name="signal-a",
                source="SRT",
                status="ACTIVE",
                bitrate_receive_mbps=6.0,
                health_status=HealthStatus.DEGRADED,
                health_reason="RTT 180 ms",
            ),
        ),
    )

    rendered = IncomingPanelRenderer().render(data)

    console = Console(
        record=True,
        width=160,
    )
    console.print(rendered)
    output = console.export_text()

    assert "Reason" in output
    assert "RTT 180 ms" in output


def test_renderer_presents_na_when_health_reason_is_unavailable() -> None:
    data = IncomingPanelData(
        rows=(
            IncomingRowData(
                path_name="signal-a",
                source="MPEG-TS",
                status="ACTIVE",
                bitrate_receive_mbps=4.5,
                health_status=HealthStatus.HEALTHY,
                health_reason=None,
            ),
        ),
    )

    rendered = IncomingPanelRenderer().render(data)

    console = Console(
        record=True,
        width=160,
    )
    console.print(rendered)
    output = console.export_text()

    assert "Reason" in output
    assert "N/A" in output


def test_renderer_presents_health_since_and_duration() -> None:
    from datetime import datetime, timedelta, timezone

    reference_at = datetime(
        2026,
        10,
        7,
        18,
        5,
        31,
        tzinfo=timezone.utc,
    )
    health_since = reference_at - timedelta(
        hours=1,
        minutes=2,
        seconds=3,
    )

    data = IncomingPanelData(
        rows=(
            IncomingRowData(
                path_name="future-service",
                source="SRT",
                status="ACTIVE",
                bitrate_receive_mbps=6.0,
                health_status=HealthStatus.HEALTHY,
                health_since=health_since,
            ),
        ),
        reference_at=reference_at,
    )

    output = _render_text(data)

    assert "Since" in output
    assert "Duration" in output
    assert "2026-10-07 17:03:28" in output
    assert "01:02:03" in output


def test_renderer_presents_na_when_health_timing_is_unavailable() -> None:
    from datetime import datetime, timezone

    reference_at = datetime(
        2026,
        10,
        7,
        18,
        5,
        31,
        tzinfo=timezone.utc,
    )

    data = IncomingPanelData(
        rows=(
            IncomingRowData(
                path_name="future-service",
                source="MPEG-TS",
                status="ACTIVE",
                bitrate_receive_mbps=4.5,
                health_status=None,
                health_since=None,
            ),
        ),
        reference_at=reference_at,
    )

    output = _render_text(data)

    assert "Since" in output
    assert "Duration" in output
    assert "N/A" in output

def test_renderer_presents_canonical_alarm_indicators() -> None:
    """Render already-projected alarm count and maximum severity."""
    from rich.table import Table

    data = IncomingPanelData(
        rows=(
            IncomingRowData(
                path_name="future-clear",
                source="SRT",
                status="ACTIVE",
                bitrate_receive_mbps=4.0,
                health_status=HealthStatus.HEALTHY,
                alarm_count=0,
                alarm_severity=None,
            ),
            IncomingRowData(
                path_name="future-major",
                source="SRT",
                status="ACTIVE",
                bitrate_receive_mbps=4.0,
                health_status=HealthStatus.DEGRADED,
                alarm_count=1,
                alarm_severity="MAJOR",
            ),
            IncomingRowData(
                path_name="future-critical",
                source="MPEG-TS",
                status="ACTIVE",
                bitrate_receive_mbps=4.0,
                health_status=HealthStatus.CRITICAL,
                alarm_count=2,
                alarm_severity="CRITICAL",
            ),
            IncomingRowData(
                path_name="future-warning",
                source="MPEG-TS",
                status="ACTIVE",
                bitrate_receive_mbps=4.0,
                health_status=HealthStatus.DEGRADED,
                alarm_count=3,
                alarm_severity="WARNING",
            ),
        ),
    )

    panel = IncomingPanelRenderer().render(data)
    table = panel.renderable

    assert isinstance(table, Table)

    columns = tuple(
        column.header
        for column in table.columns
    )

    assert "Alarms" in columns
    assert columns.index("Alarms") == columns.index("Health") + 1

    alarm_column = table.columns[
        columns.index("Alarms")
    ]

    assert tuple(alarm_column.cells) == (
        "—",
        "1 MAJOR",
        "2 CRITICAL",
        "3 WARNING",
    )
