"""Functional projection tests for observed incoming stability."""

from datetime import datetime, timezone

from app.dashboard.services.dashboard_service import DashboardService
from app.dashboard.services.incoming_path_stability_tracker import (
    IncomingPathStability,
)
from app.domain.sessions import SessionSnapshot
from app.domain.streaming import (
    MeasurementQuality,
    MediaMTXSnapshot,
    MediaPath,
    MediaPathStatus,
    MediaSource,
    StreamingMeasurement,
)


CAPTURED_AT = datetime(
    2026, 10, 29, 12, 0, 0,
    tzinfo=timezone.utc,
)


def make_path(name):
    return MediaPath(
        name=name,
        configuration_name=name,
        status=MediaPathStatus.ACTIVE,
        ready=True,
        available=True,
        online=True,
        source=MediaSource(
            source_type="mpegtsSource",
            source_id=f"{name}-source",
        ),
    )


def build_panel(stability):
    paths = (
        make_path("impact"),
        make_path("ejtv"),
        make_path("enlace"),
    )

    snapshot = MediaMTXSnapshot(
        captured_at=CAPTURED_AT,
        paths=paths,
        reported_item_count=len(paths),
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

    sessions = SessionSnapshot(
        captured_at=CAPTURED_AT,
        sessions=(),
    )

    return DashboardService().build_incoming_panel(
        snapshot=snapshot,
        measurement=measurement,
        session_snapshot=sessions,
        health=None,
        incoming_path_stability=stability,
    )


def test_projects_independent_observed_counters():
    stability = {
        "impact": IncomingPathStability(
            interruptions=2,
            recoveries=1,
        ),
        "ejtv": IncomingPathStability(
            interruptions=0,
            recoveries=0,
        ),
        "enlace": IncomingPathStability(
            interruptions=3,
            recoveries=2,
        ),
    }

    panel = build_panel(stability)

    rows = {
        row.path_name: row
        for row in panel.rows
    }

    assert set(rows) == {
        "impact",
        "ejtv",
        "enlace",
    }

    assert (
        rows["impact"].transport_observed_interruptions
        == 2
    )
    assert (
        rows["impact"].transport_observed_recoveries
        == 1
    )

    assert (
        rows["ejtv"].transport_observed_interruptions
        == 0
    )
    assert (
        rows["ejtv"].transport_observed_recoveries
        == 0
    )

    assert (
        rows["enlace"].transport_observed_interruptions
        == 3
    )
    assert (
        rows["enlace"].transport_observed_recoveries
        == 2
    )


def test_missing_stability_evidence_is_unknown():
    panel = build_panel(None)

    assert len(panel.rows) == 3

    for row in panel.rows:
        assert row.transport_observed_interruptions is None
        assert row.transport_observed_recoveries is None


def test_partial_stability_evidence_preserves_unknown_paths():
    panel = build_panel({
        "impact": IncomingPathStability(
            interruptions=1,
            recoveries=1,
        )
    })

    rows = {
        row.path_name: row
        for row in panel.rows
    }

    assert rows["impact"].transport_observed_interruptions == 1
    assert rows["impact"].transport_observed_recoveries == 1

    for name in ("ejtv", "enlace"):
        assert rows[name].transport_observed_interruptions is None
        assert rows[name].transport_observed_recoveries is None
