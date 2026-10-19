"""RED contract for real INCOMING transport renderer evidence."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone

from rich.console import Console

from app.dashboard.models.incoming_panel import (
    IncomingPanelData,
    IncomingRowData,
)
from app.dashboard.renderers.incoming_transport_cards_renderer import (
    IncomingTransportCardsRenderer,
)
from app.domain.streaming.health import HealthStatus


NOW = datetime(2026, 10, 19, 16, 0, tzinfo=timezone.utc)


def render_row(row: IncomingRowData) -> str:
    data = IncomingPanelData(
        rows=(row,),
        reference_at=NOW,
    )

    panel = IncomingTransportCardsRenderer().render(
        data,
        selected_path_name=row.path_name,
    )

    console = Console(
        width=140,
        force_terminal=False,
        color_system=None,
    )

    with console.capture() as capture:
        console.print(panel)

    return capture.get()


def make_row(**changes) -> IncomingRowData:
    row = IncomingRowData(
        path_name="impact",
        source="SRT",
        protocol="SRT",
        status="ACTIVE",
        bitrate_receive_mbps=5.87,
        health_status=HealthStatus.DEGRADED,
        transport_health_status=HealthStatus.HEALTHY,
        transport_source_type="srtSource",
        transport_ready=True,
        transport_available=True,
        transport_online=True,
        transport_received_bytes=58_566_181_475,
        transport_inbound_frames_in_error=0,
        transport_observed_at=NOW - timedelta(hours=48),
        transport_health_since=NOW - timedelta(days=3),
    )

    return replace(row, **changes)


def test_connection_shows_real_source_type() -> None:
    screen = render_row(make_row())

    assert "Connection Mode" in screen
    assert "srtSource" in screen


def test_traffic_shows_received_bytes() -> None:
    screen = render_row(make_row())

    assert "Received Data" in screen
    assert "58,566,181,475" in screen


def test_stability_shows_actual_availability() -> None:
    available_screen = render_row(
        make_row(transport_available=True)
    )

    unavailable_screen = render_row(
        make_row(transport_available=False)
    )

    assert "Availability" in available_screen
    assert "YES" in available_screen
    assert "NO" in unavailable_screen


def test_health_shows_canonical_evidence_age() -> None:
    screen = render_row(make_row())

    assert "Evidence Age" in screen
    assert "48h" in screen


def test_health_shows_last_evaluation_timestamp() -> None:
    screen = render_row(make_row())

    assert "Last Evaluation" in screen
    assert "2026-10-17" in screen


def test_missing_evidence_remains_unavailable() -> None:
    screen = render_row(
        make_row(
            transport_source_type=None,
            transport_available=None,
            transport_received_bytes=None,
            transport_observed_at=None,
        )
    )

    assert "N/A" in screen
    assert "srtSource" not in screen


def test_transport_duration_is_not_aggregate_duration() -> None:
    screen = render_row(make_row())

    assert "Duration" in screen
    assert "72h" not in screen
