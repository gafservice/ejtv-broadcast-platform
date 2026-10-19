"""RED tests for incoming transport evidence projection."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone

from app.dashboard.services.dashboard_service import DashboardService
from app.domain.sessions import SessionSnapshot
from app.domain.streaming import (
    MediaMTXSnapshot,
    MediaPath,
    MediaPathStatus,
    MediaSource,
    MeasurementQuality,
    StreamingMeasurement,
)
from app.noc.current_state.signal_health_current_state import (
    SignalHealthCurrentState,
)

from tests.dashboard.test_incoming_transport_health_projection import (
    CAPTURED_AT,
    make_state,
)


def build_panel(
    *,
    media_path: MediaPath,
    states: tuple[SignalHealthCurrentState, ...] = (),
):
    snapshot = MediaMTXSnapshot(
        captured_at=CAPTURED_AT,
        paths=(media_path,),
        reported_item_count=1,
        reported_page_count=1,
    )

    measurement = StreamingMeasurement(
        captured_at=CAPTURED_AT,
        previous_captured_at=CAPTURED_AT,
        interval_seconds=1.0,
        paths=(),
        total_inbound_bitrate_bps=0.0,
        total_outbound_bitrate_bps=0.0,
        quality=MeasurementQuality.AVAILABLE,
    )

    return DashboardService().build_incoming_panel(
        snapshot=snapshot,
        measurement=measurement,
        session_snapshot=SessionSnapshot(
            captured_at=CAPTURED_AT,
            sessions=(),
        ),
        health=None,
        signal_health_current_states=states,
    )


def make_path(
    *,
    ready: bool = True,
    available: bool = True,
    online: bool = True,
    inbound_bytes: int = 58_566_181_475,
    inbound_frames_in_error: int = 0,
) -> MediaPath:
    return MediaPath(
        name="impact",
        configuration_name="impact",
        status=(
            MediaPathStatus.ACTIVE
            if ready and available and online
            else MediaPathStatus.OFFLINE
        ),
        ready=ready,
        available=available,
        online=online,
        ready_time=CAPTURED_AT - timedelta(hours=2),
        available_time=CAPTURED_AT - timedelta(hours=2),
        online_time=CAPTURED_AT - timedelta(hours=1),
        source=MediaSource(
            source_type="srtSource",
            source_id="impact-source",
        ),
        readers=(),
        inbound_bytes=inbound_bytes,
        outbound_bytes=0,
        inbound_frames_in_error=inbound_frames_in_error,
    )


def test_projects_mediamtx_transport_evidence() -> None:
    path = make_path(
        inbound_bytes=58_566_181_475,
        inbound_frames_in_error=7,
    )

    row = build_panel(media_path=path).rows[0]

    assert row.transport_source_type == "srtSource"
    assert row.transport_ready is True
    assert row.transport_available is True
    assert row.transport_online is True
    assert row.transport_available_since == path.available_time
    assert row.transport_online_since == path.online_time
    assert row.transport_received_bytes == 58_566_181_475
    assert row.transport_inbound_frames_in_error == 7


def test_preserves_false_and_zero_transport_evidence() -> None:
    path = make_path(
        ready=False,
        available=False,
        online=False,
        inbound_bytes=0,
        inbound_frames_in_error=0,
    )

    row = build_panel(media_path=path).rows[0]

    assert row.transport_ready is False
    assert row.transport_available is False
    assert row.transport_online is False
    assert row.transport_received_bytes == 0
    assert row.transport_inbound_frames_in_error == 0


def test_projects_unique_canonical_timestamps() -> None:
    state = make_state()
    state = replace(
        state,
        observed_at=CAPTURED_AT,
        health_since=CAPTURED_AT - timedelta(minutes=20),
    )

    row = build_panel(
        media_path=make_path(),
        states=(state,),
    ).rows[0]

    assert row.transport_observed_at == state.observed_at
    assert row.transport_health_since == state.health_since


def test_missing_canonical_state_keeps_timestamps_unknown() -> None:
    row = build_panel(
        media_path=make_path(),
        states=(),
    ).rows[0]

    assert row.transport_observed_at is None
    assert row.transport_health_since is None


def test_ambiguous_canonical_state_keeps_timestamps_unknown() -> None:
    first = make_state(profile_id="impact-main")

    second = replace(
        first,
        profile_id="impact-secondary",
        health=replace(
            first.health,
            profile_id="impact-secondary",
        ),
    )

    row = build_panel(
        media_path=make_path(),
        states=(first, second),
    ).rows[0]

    assert row.transport_health_status is None
    assert row.transport_observed_at is None
    assert row.transport_health_since is None
