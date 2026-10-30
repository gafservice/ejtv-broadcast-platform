"""SRT incoming retransmissions attribution and rendering contract."""

from datetime import UTC, datetime

import pytest

from app.dashboard.renderers.incoming_transport_cards_renderer import (
    IncomingTransportCardsRenderer,
)
from app.domain.sessions import SessionRole
from app.domain.streaming.media_observation import EvidenceAvailability
from app.domain.streaming.transport_quality_observation import (
    TransportMetricObservation,
    TransportQualityObservation,
)


OBSERVED_AT = datetime(2026, 10, 29, 12, 0, tzinfo=UTC)

METRIC_NAME = "srt.connection.receive.retransmitted_packets"


def make_observation(
    *,
    role=SessionRole.PUBLISHER,
    connection_id="conn-1",
    source_id="conn-1",
    include_metric=True,
):
    metrics = ()

    if include_metric:
        metrics = (
            TransportMetricObservation(
                metric_name=METRIC_NAME,
                value=12,
                unit="packets",
                availability=EvidenceAvailability.AVAILABLE,
                source="mediamtx.metrics",
                direction=None,
                connection_id=connection_id,
                connection_role=role,
                measurement_scope="CONNECTION",
            ),
        )

    return TransportQualityObservation(
        service_id="impact-main",
        path_name="impact",
        source_type="srtConn",
        source_id=source_id,
        observed_at=OBSERVED_AT,
        availability=(
            EvidenceAvailability.AVAILABLE
            if metrics
            else EvidenceAvailability.UNAVAILABLE
        ),
        metrics=metrics,
    )


@pytest.mark.parametrize(
    "role,connection_id,source_id,include_metric,expected",
    [
        (SessionRole.PUBLISHER, "conn-1", "conn-1", True, 12),
        (SessionRole.READER, "conn-1", "conn-1", True, None),
        (SessionRole.PUBLISHER, "conn-2", "conn-1", True, None),
        (SessionRole.PUBLISHER, "conn-1", "conn-1", False, None),
    ],
)
def test_retransmissions_attribution(
    role,
    connection_id,
    source_id,
    include_metric,
    expected,
):
    observation = make_observation(
        role=role,
        connection_id=connection_id,
        source_id=source_id,
        include_metric=include_metric,
    )

    metric = (
        IncomingTransportCardsRenderer
        ._select_srt_ingress_receive_metric(
            observation,
            metric_name=METRIC_NAME,
            unit="packets",
        )
    )

    if expected is None:
        assert metric is None
    else:
        assert metric is not None
        assert metric.value == expected
