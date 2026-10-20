"""Full-cycle resilience contract for optional Transport Quality."""

from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import pytest

from app.adapters.mediamtx.metrics_acquisition import (
    MediaMTXMetricsAcquisition,
)
from app.adapters.mediamtx.metrics_parser import MediaMTXMetricsParser
from app.dashboard.application import DashboardApplication
from app.dashboard.models import DashboardData
from app.domain.streaming import (
    MediaMTXSnapshot,
    MediaPath,
    MediaPathStatus,
    MediaSource,
)
from app.domain.streaming.evidence_acquisition_interval import (
    EvidenceAcquisitionInterval,
)
from app.domain.streaming.expected_media_profile import (
    ExpectedMediaProfile,
)
from app.domain.streaming.media_observation import (
    EvidenceAvailability,
)
from app.domain.streaming.transport_quality_observation import (
    TransportQualityObservation,
)


CAPTURED_AT = datetime(2026, 10, 20, 12, 0, tzinfo=UTC)


def make_acquisition(observed_at):
    return MediaMTXMetricsAcquisition(
        snapshot=MediaMTXMetricsParser().parse(
            'srt_conns_ms_rtt'
            '{id="reader-1",path="ejtv",state="read"} 12.5'
        ),
        interval=EvidenceAcquisitionInterval(
            started_at=observed_at,
            completed_at=observed_at + timedelta(milliseconds=50),
            source="mediamtx.metrics",
        ),
    )


def make_application(
    *,
    paths,
    profiles,
    acquisition_service,
    producer,
):
    media_snapshot = MediaMTXSnapshot(
        captured_at=CAPTURED_AT,
        paths=tuple(paths),
        reported_item_count=len(paths),
        reported_page_count=1,
    )

    mediamtx_adapter = Mock()
    mediamtx_adapter.health.return_value = True
    mediamtx_adapter.get_snapshot.return_value = media_snapshot
    mediamtx_adapter.get_source_configurations.return_value = {}

    session_snapshot = Mock()
    session_snapshot.sessions = ()

    session_adapter = Mock()
    session_adapter.get_snapshot.return_value = session_snapshot

    streaming_service = Mock()
    streaming_service.compare.return_value.paths = ()

    session_service = Mock()
    session_service.measure.return_value = Mock()

    system_service = Mock()
    system_service.get_system_info.return_value.hostname = "ejtv-01"

    health_service = Mock()
    health_service.build.return_value = Mock()

    dashboard_data = Mock(spec=DashboardData)
    dashboard_data.incoming = None
    dashboard_data.active_connections = None
    dashboard_data.active_alarms = None
    dashboard_data.recent_events = None

    snapshot_service = Mock()
    snapshot_service.build_snapshot.return_value = dashboard_data

    application = DashboardApplication(
        mediamtx_adapter=mediamtx_adapter,
        session_adapter=session_adapter,
        streaming_service=streaming_service,
        session_service=session_service,
        dashboard_service=Mock(),
        dashboard_renderer=Mock(),
        system_service=system_service,
        metrics_client=Mock(),
        metrics_parser=Mock(),
        metrics_acquisition_service=acquisition_service,
        streaming_health_service=health_service,
        transport_quality_producer=producer,
        dashboard_snapshot_service=snapshot_service,
        network_telemetry_service=Mock(),
        media_profiles=tuple(profiles),
    )

    return (
        application,
        mediamtx_adapter,
        health_service,
        snapshot_service,
    )


def make_path(name="ejtv", *, with_source=True):
    return MediaPath(
        name=name,
        configuration_name=name,
        status=MediaPathStatus.ACTIVE,
        ready=True,
        available=True,
        online=True,
        source=(
            MediaSource(source_type="udpSource")
            if with_source
            else None
        ),
    )


def make_profile(name="ejtv", *, path_name="ejtv"):
    return ExpectedMediaProfile(
        profile_id=f"{name}-main",
        service_id=name,
        path_name=path_name,
    )


@pytest.mark.parametrize(
    ("paths", "profiles"),
    [
        ((), (make_profile(),)),
        ((make_path(with_source=False),), (make_profile(),)),
        ((make_path(),), (make_profile(path_name=None),)),
    ],
)
def test_missing_source_or_path_does_not_invent_observations(
    paths,
    profiles,
):
    acquisition_service = Mock()
    acquisition_service.acquire.return_value = make_acquisition(
        CAPTURED_AT
    )

    producer = Mock()

    application, _, health_service, snapshot_service = (
        make_application(
            paths=paths,
            profiles=profiles,
            acquisition_service=acquisition_service,
            producer=producer,
        )
    )

    application.build_dashboard()

    acquisition_service.acquire.assert_called_once_with()
    producer.build.assert_not_called()
    health_service.build.assert_called_once()

    snapshot_input = (
        snapshot_service.build_snapshot.call_args.args[0]
    )

    assert snapshot_input.transport_quality_observations == ()


def test_failed_acquisition_does_not_reuse_previous_evidence():
    acquisition_service = Mock()
    acquisition_service.acquire.side_effect = (
        make_acquisition(CAPTURED_AT),
        RuntimeError("metrics unavailable"),
    )

    producer = Mock()

    producer.build.return_value = TransportQualityObservation(
        service_id="ejtv",
        path_name="ejtv",
        source_type="udpSource",
        observed_at=CAPTURED_AT,
        availability=EvidenceAvailability.UNAVAILABLE,
    )

    application, _, _, snapshot_service = make_application(
        paths=(make_path(),),
        profiles=(make_profile(),),
        acquisition_service=acquisition_service,
        producer=producer,
    )

    application.build_dashboard()

    with pytest.raises(RuntimeError, match="metrics unavailable"):
        application.build_dashboard()

    assert acquisition_service.acquire.call_count == 2
    assert producer.build.call_count == 1
    assert snapshot_service.build_snapshot.call_count == 1


def test_consecutive_cycles_use_new_acquisitions():
    first = make_acquisition(CAPTURED_AT)
    second = make_acquisition(
        CAPTURED_AT + timedelta(seconds=5)
    )

    acquisition_service = Mock()
    acquisition_service.acquire.side_effect = (
        first,
        second,
    )

    producer = Mock()

    def build_observation(**kwargs):
        return TransportQualityObservation(
            service_id=kwargs["service_id"],
            path_name=kwargs["path_name"],
            source_type=kwargs["source_type"],
            observed_at=kwargs["observed_at"],
            availability=EvidenceAvailability.UNAVAILABLE,
            acquisition_interval=kwargs["acquisition_interval"],
        )

    producer.build.side_effect = build_observation

    application, _, health_service, snapshot_service = (
        make_application(
            paths=(make_path(),),
            profiles=(make_profile(),),
            acquisition_service=acquisition_service,
            producer=producer,
        )
    )

    application.build_dashboard()
    application.build_dashboard()

    assert acquisition_service.acquire.call_count == 2
    assert producer.build.call_count == 2
    assert health_service.build.call_count == 2

    first_call, second_call = producer.build.call_args_list

    assert first_call.kwargs["snapshot"] is first.snapshot
    assert second_call.kwargs["snapshot"] is second.snapshot

    assert (
        first_call.kwargs["acquisition_interval"]
        is first.interval
    )
    assert (
        second_call.kwargs["acquisition_interval"]
        is second.interval
    )

    assert snapshot_service.build_snapshot.call_count == 2


def test_disabled_producer_keeps_legacy_health_route():
    acquisition_service = Mock()
    acquisition_service.acquire.return_value = make_acquisition(
        CAPTURED_AT
    )

    application, _, health_service, snapshot_service = (
        make_application(
            paths=(make_path(),),
            profiles=(make_profile(),),
            acquisition_service=acquisition_service,
            producer=None,
        )
    )

    application.build_dashboard()

    acquisition_service.acquire.assert_called_once_with()
    health_service.build.assert_called_once()

    snapshot_input = (
        snapshot_service.build_snapshot.call_args.args[0]
    )

    assert snapshot_input.transport_quality_observations == ()
