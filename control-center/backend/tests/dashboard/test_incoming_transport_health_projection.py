"""RED contract for canonical INCOMING Transport Health projection."""

from dataclasses import replace
from datetime import datetime, timezone

from app.dashboard.services.dashboard_service import DashboardService
from app.domain.sessions import SessionSnapshot
from app.domain.streaming import (
    HealthStatus,
    MediaMTXSnapshot,
    MediaPath,
    MediaPathStatus,
    MediaSource,
    MeasurementQuality,
    StreamingMeasurement,
)
from app.domain.streaming.signal_health import SignalHealth
from app.noc.current_state.signal_health_current_state import (
    SignalHealthCurrentState,
)


CAPTURED_AT = datetime(
    2026, 10, 19, 12, 0, tzinfo=timezone.utc
)


def make_state(
    *,
    profile_id="impact-main",
    media_status=HealthStatus.DEGRADED,
    transport_status=HealthStatus.HEALTHY,
    status=HealthStatus.DEGRADED,
):
    return SignalHealthCurrentState(
        profile_id=profile_id,
        service_id="impact",
        path_name="impact",
        observed_at=CAPTURED_AT,
        health_since=CAPTURED_AT,
        health=SignalHealth(
            profile_id=profile_id,
            service_id="impact",
            path_name="impact",
            media_status=media_status,
            transport_status=transport_status,
            status=status,
        ),
    )


def build_panel(states):
    media_path = MediaPath(
        name="impact",
        configuration_name="impact",
        status=MediaPathStatus.ACTIVE,
        ready=True,
        available=True,
        online=True,
        source=MediaSource(
            source_type="srtSource",
            source_id="source-impact",
        ),
        readers=(),
        inbound_bytes=1_000_000,
        outbound_bytes=0,
    )

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
        signal_health_current_states=tuple(states),
    )


def test_transport_health_is_independent_from_signal_health():
    panel = build_panel((make_state(),))
    row = panel.rows[0]

    assert row.health_status is HealthStatus.DEGRADED
    assert row.transport_health_status is HealthStatus.HEALTHY


def test_transport_health_is_unavailable_without_canonical_state():
    panel = build_panel(())
    row = panel.rows[0]

    assert row.health_status is None
    assert row.transport_health_status is None


def test_transport_health_rejects_ambiguous_path_identity():
    first = make_state(
        profile_id="impact-main",
        transport_status=HealthStatus.HEALTHY,
    )

    second = replace(
        first,
        profile_id="impact-secondary",
        health=replace(
            first.health,
            profile_id="impact-secondary",
            transport_status=HealthStatus.CRITICAL,
            status=HealthStatus.CRITICAL,
        ),
    )

    panel = build_panel((first, second))
    row = panel.rows[0]

    assert row.transport_health_status is None


def test_transport_health_rejects_reversed_ambiguous_states():
    first = make_state(
        profile_id="impact-main",
        transport_status=HealthStatus.HEALTHY,
    )

    second = replace(
        first,
        profile_id="impact-secondary",
        health=replace(
            first.health,
            profile_id="impact-secondary",
            transport_status=HealthStatus.CRITICAL,
            status=HealthStatus.CRITICAL,
        ),
    )

    panel = build_panel((second, first))
    row = panel.rows[0]

    assert row.transport_health_status is None
