"""Transport Quality evidence projection into DashboardData."""

from dataclasses import fields
from datetime import UTC, datetime, timedelta

from app.dashboard.models.dashboard_models import (
    DashboardData,
    ServerPanelData,
    StreamingPanelData,
)
from app.dashboard.services.dashboard_service import DashboardService
from app.dashboard.services.dashboard_snapshot_service import (
    DashboardSnapshotInput,
    DashboardSnapshotService,
)
from app.domain.streaming import (
    MeasurementQuality,
    MediaMTXSnapshot,
    StreamingMeasurement,
)
from app.domain.streaming.evidence_acquisition_interval import (
    EvidenceAcquisitionInterval,
)
from app.domain.streaming.media_observation import EvidenceAvailability
from app.domain.streaming.transport_quality_observation import (
    TransportMetricObservation,
    TransportQualityObservation,
)


CAPTURED_AT = datetime(2026, 10, 20, 12, 0, tzinfo=UTC)


def make_evidence():
    interval = EvidenceAcquisitionInterval(
        started_at=CAPTURED_AT,
        completed_at=CAPTURED_AT + timedelta(milliseconds=50),
        source="mediamtx.metrics",
    )

    metric = TransportMetricObservation(
        metric_name="srt.connection.rtt",
        value=12.5,
        unit="ms",
        availability=EvidenceAvailability.AVAILABLE,
        source="mediamtx.metrics",
        connection_id="reader-1",
        measurement_scope="CONNECTION",
    )

    ejtv = TransportQualityObservation(
        service_id="ejtv",
        path_name="ejtv",
        source_type="udpSource",
        observed_at=CAPTURED_AT,
        availability=EvidenceAvailability.AVAILABLE,
        metrics=(metric,),
        acquisition_interval=interval,
    )

    enlace = TransportQualityObservation(
        service_id="enlace",
        path_name="enlace",
        source_type="udpSource",
        observed_at=CAPTURED_AT,
        availability=EvidenceAvailability.UNAVAILABLE,
        acquisition_interval=interval,
    )

    return ejtv, enlace


def make_snapshot_input(observations=()):
    snapshot = MediaMTXSnapshot(
        captured_at=CAPTURED_AT,
        paths=(),
        reported_item_count=0,
        reported_page_count=0,
    )

    measurement = StreamingMeasurement(
        captured_at=CAPTURED_AT,
        previous_captured_at=None,
        interval_seconds=None,
        paths=(),
        total_inbound_bitrate_bps=None,
        total_outbound_bitrate_bps=None,
        quality=MeasurementQuality.NOT_AVAILABLE,
    )

    return DashboardSnapshotInput(
        hostname="ejtv-01",
        mediamtx_online=True,
        api_online=True,
        snapshot=snapshot,
        measurement=measurement,
        transport_quality_observations=observations,
    )


def test_dashboard_data_declares_optional_transport_quality():
    field_names = {field.name for field in fields(DashboardData)}

    assert "transport_quality_observations" in field_names


def test_snapshot_projection_preserves_transport_quality_identity():
    observations = make_evidence()

    result = DashboardSnapshotService().build_snapshot(
        make_snapshot_input(observations)
    )

    assert result.transport_quality_observations is observations
    assert result.transport_quality_observations[0] is observations[0]
    assert result.transport_quality_observations[1] is observations[1]

    assert (
        result.transport_quality_observations[0].metrics[0]
        is observations[0].metrics[0]
    )

    assert (
        result.transport_quality_observations[0].acquisition_interval
        is observations[0].acquisition_interval
    )


def test_snapshot_projection_defaults_to_empty_tuple():
    result = DashboardSnapshotService().build_snapshot(
        make_snapshot_input()
    )

    assert result.transport_quality_observations == ()


def test_direct_dashboard_builder_preserves_evidence():
    observations = make_evidence()

    server = ServerPanelData(
        hostname="ejtv-01",
        mediamtx_online=True,
        api_online=True,
        snapshot_at=CAPTURED_AT,
        quality="AVAILABLE",
    )

    streaming = StreamingPanelData(
        active_paths=0,
        readers=0,
        inbound_bitrate_bps=None,
        outbound_bitrate_bps=None,
        quality="NOT_AVAILABLE",
    )

    result = DashboardService().build_dashboard(
        server=server,
        streaming=streaming,
        paths=(),
        transport_quality_observations=observations,
    )

    assert result.transport_quality_observations is observations
