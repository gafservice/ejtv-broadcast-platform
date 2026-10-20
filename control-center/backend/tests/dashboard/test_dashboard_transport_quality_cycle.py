"""Full dashboard-cycle contract for shared transport evidence."""

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
from app.domain.streaming.expected_media_profile import ExpectedMediaProfile
from app.domain.streaming.media_observation import EvidenceAvailability
from app.domain.streaming.transport_quality_observation import (
    TransportQualityObservation,
)


CAPTURED_AT = datetime(2026, 10, 20, 12, 0, tzinfo=UTC)


def test_full_cycle_shares_acquisition_and_delivers_transport_quality():
    media_path = MediaPath(
        name="ejtv",
        configuration_name="ejtv",
        status=MediaPathStatus.ACTIVE,
        ready=True,
        available=True,
        online=True,
        source=MediaSource(source_type="udpSource"),
    )

    media_snapshot = MediaMTXSnapshot(
        captured_at=CAPTURED_AT,
        paths=(media_path,),
        reported_item_count=1,
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
    measurement = Mock()
    measurement.paths = ()
    streaming_service.compare.return_value = measurement

    session_service = Mock()
    session_service.measure.return_value = Mock()

    system_service = Mock()
    system_service.get_system_info.return_value.hostname = "ejtv-01"

    shared_acquisition = Mock()
    shared_acquisition.acquire.return_value = acquisition

    health_service = Mock()
    health_service.build.return_value = Mock()

    producer = Mock()
    observation = TransportQualityObservation(
        service_id="ejtv",
        path_name="ejtv",
        source_type="udpSource",
        observed_at=CAPTURED_AT,
        availability=EvidenceAvailability.UNAVAILABLE,
        acquisition_interval=acquisition.interval,
    )
    producer.build.return_value = observation

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
        media_profiles=(
            ExpectedMediaProfile(
                profile_id="ejtv-main",
                service_id="ejtv",
                path_name="ejtv",
            ),
        ),
    )

    assert application.build_dashboard() is dashboard_data

    shared_acquisition.acquire.assert_called_once_with()

    health_service.build.assert_called_once()
    assert (
        health_service.build.call_args.kwargs["snapshot"]
        is acquisition.snapshot
    )

    producer.build.assert_called_once_with(
        snapshot=acquisition.snapshot,
        observed_at=CAPTURED_AT,
        service_id="ejtv",
        path_name="ejtv",
        source_type="udpSource",
        source_id=None,
        session_snapshot=session_snapshot,
        acquisition_interval=acquisition.interval,
    )

    snapshot_service.build_snapshot.assert_called_once()
    snapshot_input = snapshot_service.build_snapshot.call_args.args[0]

    assert snapshot_input.transport_quality_observations == (
        observation,
    )
