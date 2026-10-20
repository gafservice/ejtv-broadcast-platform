"""RED contract for injecting preacquired MediaMTX metrics into Health."""

from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

from app.adapters.mediamtx.metrics_acquisition import (
    MediaMTXMetricsAcquisition,
)
from app.adapters.mediamtx.metrics_parser import (
    MediaMTXMetricsParser,
)
from app.dashboard.application import DashboardApplication
from app.domain.streaming.evidence_acquisition_interval import (
    EvidenceAcquisitionInterval,
)


CAPTURED_AT = datetime(2026, 10, 20, 12, 0, tzinfo=UTC)

ACQUISITION = MediaMTXMetricsAcquisition(
    snapshot=MediaMTXMetricsParser().parse(
        'srt_conns_ms_rtt'
        '{id="conn-1",path="ejtv",state="read"} 12.5'
    ),
    interval=EvidenceAcquisitionInterval(
        started_at=CAPTURED_AT,
        completed_at=CAPTURED_AT + timedelta(milliseconds=50),
        source="mediamtx.metrics",
    ),
)


def make_application():
    shared = Mock()
    client = Mock()
    parser = Mock()
    health = Mock()
    stabilizer = Mock()

    application = DashboardApplication(
        mediamtx_adapter=Mock(),
        session_adapter=Mock(),
        streaming_service=Mock(),
        session_service=Mock(),
        dashboard_service=Mock(),
        dashboard_renderer=Mock(),
        system_service=Mock(),
        metrics_client=client,
        metrics_parser=parser,
        metrics_acquisition_service=shared,
        streaming_health_service=health,
        streaming_health_stabilizer=stabilizer,
    )

    return application, shared, client, parser, health, stabilizer


def test_preacquired_snapshot_is_used_by_identity():
    application, _, _, _, health, _ = make_application()
    session_snapshot = Mock()

    application._build_streaming_health(
        captured_at=CAPTURED_AT,
        session_snapshot=session_snapshot,
        acquisition=ACQUISITION,
    )

    health.build.assert_called_once_with(
        snapshot=ACQUISITION.snapshot,
        captured_at=CAPTURED_AT,
        session_snapshot=session_snapshot,
        previous_session_snapshot=None,
    )

    assert (
        health.build.call_args.kwargs["snapshot"]
        is ACQUISITION.snapshot
    )


def test_preacquired_metrics_do_not_trigger_another_acquisition():
    application, shared, client, parser, _, _ = make_application()

    application._build_streaming_health(
        captured_at=CAPTURED_AT,
        session_snapshot=Mock(),
        acquisition=ACQUISITION,
    )

    shared.acquire.assert_not_called()
    client.get_metrics_text.assert_not_called()
    parser.parse.assert_not_called()


def test_preacquired_metrics_preserve_stabilization():
    application, _, _, _, health, stabilizer = make_application()

    result = application._build_streaming_health(
        captured_at=CAPTURED_AT,
        session_snapshot=Mock(),
        acquisition=ACQUISITION,
    )

    stabilizer.stabilize.assert_called_once_with(
        health.build.return_value
    )

    assert result is stabilizer.stabilize.return_value


def test_preacquired_metrics_preserve_cycle_timestamp():
    application, _, _, _, health, _ = make_application()

    different_cycle_time = CAPTURED_AT - timedelta(seconds=2)

    application._build_streaming_health(
        captured_at=different_cycle_time,
        session_snapshot=Mock(),
        acquisition=ACQUISITION,
    )

    assert (
        health.build.call_args.kwargs["captured_at"]
        is different_cycle_time
    )


def test_without_preacquisition_keeps_shared_route():
    application, shared, _, _, health, _ = make_application()

    shared.acquire.return_value = ACQUISITION

    application._build_streaming_health(
        captured_at=CAPTURED_AT,
        session_snapshot=Mock(),
    )

    shared.acquire.assert_called_once_with()

    assert (
        health.build.call_args.kwargs["snapshot"]
        is ACQUISITION.snapshot
    )
