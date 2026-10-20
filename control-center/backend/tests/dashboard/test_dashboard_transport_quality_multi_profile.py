"""Multi-profile Transport Quality integration contract."""

from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

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


def test_three_profiles_share_one_metrics_acquisition():
    source_types = {
        "impact": "srtConn",
        "ejtv": "udpSource",
        "enlace": "udpSource",
    }

    media_paths = tuple(
        MediaPath(
            name=name,
            configuration_name=name,
            status=MediaPathStatus.ACTIVE,
            ready=True,
            available=True,
            online=True,
            source=MediaSource(source_type=source_type),
        )
        for name, source_type in source_types.items()
    )

    media_snapshot = MediaMTXSnapshot(
        captured_at=CAPTURED_AT,
        paths=media_paths,
        reported_item_count=3,
        reported_page_count=1,
    )

    acquisition = MediaMTXMetricsAcquisition(
        snapshot=MediaMTXMetricsParser().parse(
            'srt_conns_ms_rtt'
            '{id="reader-1",path="ejtv",state="read"} 12.5'
        ),
        interval=EvidenceAcquisitionInterval(
            started_at=CAPTURED_AT,
            completed_at=CAPTURED_AT + timedelta(milliseconds=50),
            source="mediamtx.metrics",
        ),
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

    shared_acquisition = Mock()
    shared_acquisition.acquire.return_value = acquisition

    health_service = Mock()
    health_service.build.return_value = Mock()

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
        metrics_acquisition_service=shared_acquisition,
        streaming_health_service=health_service,
        transport_quality_producer=producer,
        dashboard_snapshot_service=snapshot_service,
        network_telemetry_service=Mock(),
        media_profiles=tuple(
            ExpectedMediaProfile(
                profile_id=f"{name}-main",
                service_id=name,
                path_name=name,
            )
            for name in source_types
        ),
    )

    assert application.build_dashboard() is dashboard_data

    shared_acquisition.acquire.assert_called_once_with()

    assert producer.build.call_count == 3

    for call in producer.build.call_args_list:
        assert call.kwargs["snapshot"] is acquisition.snapshot
        assert call.kwargs["acquisition_interval"] is acquisition.interval
        assert call.kwargs["session_snapshot"] is session_snapshot

    assert (
        health_service.build.call_args.kwargs["snapshot"]
        is acquisition.snapshot
    )

    snapshot_input = snapshot_service.build_snapshot.call_args.args[0]

    observations = snapshot_input.transport_quality_observations

    assert len(observations) == 3

    assert {
        (item.service_id, item.path_name, item.source_type)
        for item in observations
    } == {
        ("impact", "impact", "srtConn"),
        ("ejtv", "ejtv", "udpSource"),
        ("enlace", "enlace", "udpSource"),
    }
