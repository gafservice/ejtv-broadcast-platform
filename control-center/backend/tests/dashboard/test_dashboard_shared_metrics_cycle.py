"""Per-cycle contract for optional shared MediaMTX acquisition."""

from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import pytest

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

PARSER = MediaMTXMetricsParser()


def acquisition(value: float, offset: int):
    observed = CAPTURED_AT + timedelta(seconds=offset)

    snapshot = PARSER.parse(
        'srt_conns_ms_rtt'
        f'{{id="conn-1",path="ejtv",state="read"}} {value}'
    )

    interval = EvidenceAcquisitionInterval(
        started_at=observed,
        completed_at=observed + timedelta(milliseconds=50),
        source="mediamtx.metrics",
    )

    return MediaMTXMetricsAcquisition(
        snapshot=snapshot,
        interval=interval,
    )


def make_application():
    shared = Mock()
    health = Mock()

    application = DashboardApplication(
        mediamtx_adapter=Mock(),
        session_adapter=Mock(),
        streaming_service=Mock(),
        session_service=Mock(),
        dashboard_service=Mock(),
        dashboard_renderer=Mock(),
        system_service=Mock(),
        metrics_client=Mock(),
        metrics_parser=Mock(),
        streaming_health_service=health,
        metrics_acquisition_service=shared,
    )

    return application, shared, health


def test_two_health_cycles_acquire_twice():
    application, shared, _ = make_application()

    shared.acquire.side_effect = [
        acquisition(10.0, 0),
        acquisition(20.0, 1),
    ]

    application._build_streaming_health(
        captured_at=CAPTURED_AT,
        session_snapshot=Mock(),
    )

    application._build_streaming_health(
        captured_at=CAPTURED_AT + timedelta(seconds=1),
        session_snapshot=Mock(),
    )

    assert shared.acquire.call_count == 2


def test_consecutive_cycles_do_not_reuse_previous_snapshot():
    application, shared, health = make_application()

    first = acquisition(10.0, 0)
    second = acquisition(20.0, 1)

    shared.acquire.side_effect = [first, second]

    application._build_streaming_health(
        captured_at=CAPTURED_AT,
        session_snapshot=Mock(),
    )

    application._build_streaming_health(
        captured_at=CAPTURED_AT + timedelta(seconds=1),
        session_snapshot=Mock(),
    )

    assert health.build.call_count == 2

    assert (
        health.build.call_args_list[0].kwargs["snapshot"]
        is first.snapshot
    )

    assert (
        health.build.call_args_list[1].kwargs["snapshot"]
        is second.snapshot
    )


def test_failed_second_acquisition_does_not_reuse_first():
    application, shared, health = make_application()

    first = acquisition(10.0, 0)

    shared.acquire.side_effect = [
        first,
        RuntimeError("second acquisition failed"),
    ]

    application._build_streaming_health(
        captured_at=CAPTURED_AT,
        session_snapshot=Mock(),
    )

    with pytest.raises(
        RuntimeError,
        match="second acquisition failed",
    ):
        application._build_streaming_health(
            captured_at=CAPTURED_AT + timedelta(seconds=1),
            session_snapshot=Mock(),
        )

    assert shared.acquire.call_count == 2
    assert health.build.call_count == 1

    assert (
        health.build.call_args_list[0].kwargs["snapshot"]
        is first.snapshot
    )
