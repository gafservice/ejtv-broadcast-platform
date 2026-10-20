"""RED contract for optional shared MediaMTX metrics acquisition."""

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

INTERVAL = EvidenceAcquisitionInterval(
    started_at=CAPTURED_AT,
    completed_at=CAPTURED_AT + timedelta(milliseconds=50),
    source="mediamtx.metrics",
)

METRICS_SNAPSHOT = MediaMTXMetricsParser().parse(
    'srt_conns_ms_rtt'
    '{id="conn-1",path="ejtv",state="read"} 12.5'
)


def make_application(*, shared=True):
    metrics_client = Mock()
    metrics_parser = Mock()
    streaming_health_service = Mock()
    streaming_health_stabilizer = Mock()

    acquisition_service = Mock()
    acquisition_service.acquire.return_value = (
        MediaMTXMetricsAcquisition(
            snapshot=METRICS_SNAPSHOT,
            interval=INTERVAL,
        )
    )

    kwargs = dict(
        mediamtx_adapter=Mock(),
        session_adapter=Mock(),
        streaming_service=Mock(),
        session_service=Mock(),
        dashboard_service=Mock(),
        dashboard_renderer=Mock(),
        system_service=Mock(),
        metrics_client=metrics_client,
        metrics_parser=metrics_parser,
        streaming_health_service=streaming_health_service,
        streaming_health_stabilizer=streaming_health_stabilizer,
    )

    if shared:
        kwargs["metrics_acquisition_service"] = acquisition_service

    application = DashboardApplication(**kwargs)

    return (
        application,
        acquisition_service,
        metrics_client,
        metrics_parser,
        streaming_health_service,
        streaming_health_stabilizer,
    )


def test_accepts_optional_shared_acquisition_dependency():
    application, *_ = make_application()

    assert application is not None


def test_shared_acquisition_runs_once_per_health_build():
    (
        application,
        acquisition_service,
        *_,
    ) = make_application()

    application._build_streaming_health(
        captured_at=CAPTURED_AT,
        session_snapshot=Mock(),
    )

    acquisition_service.acquire.assert_called_once_with()


def test_streaming_health_receives_shared_snapshot_identity():
    (
        application,
        _,
        _,
        _,
        streaming_health_service,
        _,
    ) = make_application()

    session_snapshot = Mock()

    application._build_streaming_health(
        captured_at=CAPTURED_AT,
        session_snapshot=session_snapshot,
    )

    streaming_health_service.build.assert_called_once_with(
        snapshot=METRICS_SNAPSHOT,
        captured_at=CAPTURED_AT,
        session_snapshot=session_snapshot,
        previous_session_snapshot=None,
    )


def test_shared_acquisition_skips_legacy_client_and_parser():
    (
        application,
        _,
        metrics_client,
        metrics_parser,
        _,
        _,
    ) = make_application()

    application._build_streaming_health(
        captured_at=CAPTURED_AT,
        session_snapshot=Mock(),
    )

    metrics_client.get_metrics_text.assert_not_called()
    metrics_parser.parse.assert_not_called()


def test_shared_acquisition_preserves_stabilization():
    (
        application,
        _,
        _,
        _,
        streaming_health_service,
        stabilizer,
    ) = make_application()

    result = application._build_streaming_health(
        captured_at=CAPTURED_AT,
        session_snapshot=Mock(),
    )

    stabilizer.stabilize.assert_called_once_with(
        streaming_health_service.build.return_value
    )

    assert result is stabilizer.stabilize.return_value


def test_shared_acquisition_failure_is_not_silenced():
    (
        application,
        acquisition_service,
        _,
        _,
        streaming_health_service,
        _,
    ) = make_application()

    acquisition_service.acquire.side_effect = (
        RuntimeError("metrics acquisition failed")
    )

    with pytest.raises(
        RuntimeError,
        match="metrics acquisition failed",
    ):
        application._build_streaming_health(
            captured_at=CAPTURED_AT,
            session_snapshot=Mock(),
        )

    streaming_health_service.build.assert_not_called()


def test_legacy_configuration_remains_supported():
    application, *_ = make_application(shared=False)

    assert application is not None
