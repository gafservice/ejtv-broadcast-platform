"""RED contract for Transport Quality in DashboardSnapshotInput."""

from dataclasses import fields
from datetime import datetime, timezone

from app.dashboard.services.dashboard_snapshot_service import (
    DashboardSnapshotInput,
)
from app.domain.streaming.media_observation import (
    EvidenceAvailability,
)
from app.domain.streaming.transport_quality_observation import (
    TransportQualityObservation,
)


def _observation(
    service_id: str,
    path_name: str,
    source_type: str,
) -> TransportQualityObservation:
    return TransportQualityObservation(
        service_id=service_id,
        path_name=path_name,
        source_type=source_type,
        observed_at=datetime.now(timezone.utc),
        availability=EvidenceAvailability.UNAVAILABLE,
    )


def test_snapshot_input_declares_transport_quality_observations():
    field_names = {
        field.name
        for field in fields(DashboardSnapshotInput)
    }

    assert "transport_quality_observations" in field_names


def test_transport_quality_snapshot_field_is_optional_tuple():
    field_by_name = {
        field.name: field
        for field in fields(DashboardSnapshotInput)
    }

    field = field_by_name["transport_quality_observations"]

    assert field.default == ()


def test_transport_quality_observations_preserve_service_identity():
    observations = (
        _observation("impact", "impact", "srtConn"),
        _observation("ejtv", "ejtv", "udpSource"),
        _observation("enlace", "enlace", "udpSource"),
    )

    assert tuple(
        (item.service_id, item.path_name)
        for item in observations
    ) == (
        ("impact", "impact"),
        ("ejtv", "ejtv"),
        ("enlace", "enlace"),
    )
