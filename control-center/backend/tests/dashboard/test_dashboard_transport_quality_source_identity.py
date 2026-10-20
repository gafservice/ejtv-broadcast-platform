"""DashboardApplication source identity propagation contract."""

from dataclasses import replace
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


def build_cycle(source_ids):
    source_types = {
        "impact": "srtConn",
        "ejtv": "udpSource",
        "enlace": "udpSource",
    }

    paths = tuple(
        MediaPath(
            name=name,
            configuration_name=name,
            status=MediaPathStatus.ACTIVE,
            ready=True,
            available=True,
            online=True,
            source=MediaSource(
                source_type=source_type,
                source_id=source_ids[name],
            ),
        )
        for name, source_type in source_types.items()
    )

    snapshot = MediaMTXSnapshot(
        captured_at=CAPTURED_AT,
        paths=paths,
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

    adapter = Mock()
    adapter.health.return_value = True
    adapter.get_snapshot.return_value = snapshot
    adapter.get_source_configurations.return_value = {}

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

    acquisition_service = Mock()
    acquisition_service.acquire.return_value = acquisition

    health_service = Mock()
    health_service.build.return_value = Mock()

    producer = Mock()

    def make_observation(**kwargs):
        return TransportQualityObservation(
            service_id=kwargs["service_id"],
            path_name=kwargs["path_name"],
            source_type=kwargs["source_type"],
            source_id=kwargs.get("source_id"),
            observed_at=kwargs["observed_at"],
            availability=EvidenceAvailability.UNAVAILABLE,
            acquisition_interval=kwargs["acquisition_interval"],
        )

    producer.build.side_effect = make_observation

    dashboard_data = Mock(spec=DashboardData)
    dashboard_data.incoming = None
    dashboard_data.active_connections = None
    dashboard_data.active_alarms = None
    dashboard_data.recent_events = None

    snapshot_service = Mock()
    snapshot_service.build_snapshot.return_value = dashboard_data

    application = DashboardApplication(
        mediamtx_adapter=adapter,
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
        media_profiles=tuple(
            ExpectedMediaProfile(
                profile_id=f"{name}-main",
                service_id=name,
                path_name=name,
            )
            for name in source_types
        ),
    )

    result = application.build_dashboard()

    assert result is dashboard_data

    return (
        producer,
        acquisition_service,
        acquisition,
        session_snapshot,
        snapshot_service,
    )


@pytest.mark.parametrize(
    "source_ids",
    (
        {
            "impact": "publisher-impact-A",
            "ejtv": "udp-ejtv-A",
            "enlace": "udp-enlace-A",
        },
        {
            "impact": None,
            "ejtv": None,
            "enlace": None,
        },
        {
            "impact": "publisher-impact-B",
            "ejtv": None,
            "enlace": "udp-enlace-B",
        },
    ),
)
def test_each_profile_receives_its_own_source_identity(source_ids):
    (
        producer,
        acquisition_service,
        acquisition,
        session_snapshot,
        snapshot_service,
    ) = build_cycle(source_ids)

    acquisition_service.acquire.assert_called_once_with()

    assert producer.build.call_count == 3

    calls = {
        call.kwargs["path_name"]: call.kwargs
        for call in producer.build.call_args_list
    }

    assert set(calls) == set(source_ids)

    for name, source_id in source_ids.items():
        assert "source_id" in calls[name]
        assert calls[name]["source_id"] == source_id

        assert calls[name]["snapshot"] is acquisition.snapshot
        assert calls[name]["acquisition_interval"] is acquisition.interval
        assert calls[name]["session_snapshot"] is session_snapshot

    snapshot_input = snapshot_service.build_snapshot.call_args.args[0]

    observations = snapshot_input.transport_quality_observations

    assert len(observations) == 3

    actual = {
        observation.path_name: observation.source_id
        for observation in observations
    }

    assert actual == source_ids
