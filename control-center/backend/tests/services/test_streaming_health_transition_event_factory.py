from datetime import UTC, datetime

import pytest

from app.domain.streaming.health import (
    HealthStatus,
    StreamingHealth,
)
from app.noc.domain.node_event import EventSeverity
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.services.health_transition_detector import (
    HealthTransitionKind,
)
from app.services.streaming_health_transition_detector import (
    StreamingHealthTransition,
)
from app.services.streaming_health_transition_event_factory import (
    StreamingHealthTransitionEventFactory,
)


TIMESTAMP = datetime(
    2026,
    9,
    7,
    1,
    0,
    tzinfo=UTC,
)


def health(status: HealthStatus) -> StreamingHealth:
    return StreamingHealth(
        captured_at=TIMESTAMP,
        paths=(),
        status=status,
        message=f"stream health is {status.value}",
    )


def transition(
    previous: HealthStatus,
    current: HealthStatus,
    kind: HealthTransitionKind,
) -> StreamingHealthTransition:
    return StreamingHealthTransition(
        previous=health(previous),
        current=health(current),
        kind=kind,
    )


@pytest.mark.parametrize(
    (
        "previous",
        "current",
        "kind",
        "event_type",
        "severity",
    ),
    (
        (
            HealthStatus.HEALTHY,
            HealthStatus.DEGRADED,
            HealthTransitionKind.DEGRADED,
            "STREAM_HEALTH_DEGRADED",
            EventSeverity.WARNING,
        ),
        (
            HealthStatus.HEALTHY,
            HealthStatus.CRITICAL,
            HealthTransitionKind.DEGRADED,
            "STREAM_HEALTH_DEGRADED",
            EventSeverity.CRITICAL,
        ),
        (
            HealthStatus.DEGRADED,
            HealthStatus.CRITICAL,
            HealthTransitionKind.DEGRADED,
            "STREAM_HEALTH_DEGRADED",
            EventSeverity.CRITICAL,
        ),
        (
            HealthStatus.CRITICAL,
            HealthStatus.DEGRADED,
            HealthTransitionKind.IMPROVED,
            "STREAM_HEALTH_IMPROVED",
            EventSeverity.NOTICE,
        ),
        (
            HealthStatus.CRITICAL,
            HealthStatus.HEALTHY,
            HealthTransitionKind.RECOVERED,
            "STREAM_HEALTH_RECOVERED",
            EventSeverity.INFO,
        ),
        (
            HealthStatus.HEALTHY,
            HealthStatus.UNKNOWN,
            HealthTransitionKind.UNKNOWN,
            "STREAM_HEALTH_UNKNOWN",
            EventSeverity.NOTICE,
        ),
        (
            HealthStatus.UNKNOWN,
            HealthStatus.HEALTHY,
            HealthTransitionKind.UNKNOWN,
            "STREAM_HEALTH_UNKNOWN",
            EventSeverity.NOTICE,
        ),
    ),
)
def test_factory_maps_transition_to_event(
    previous,
    current,
    kind,
    event_type,
    severity,
):
    factory = StreamingHealthTransitionEventFactory()

    event = factory.create(
        transition=transition(
            previous,
            current,
            kind,
        ),
        source=NodeInstanceId("streaming-primary"),
        timestamp=TIMESTAMP,
    )

    assert event.event_type == event_type
    assert event.severity is severity

    assert event.attributes is not None
    assert event.attributes["previous"] == previous.value
    assert event.attributes["current"] == current.value
    assert event.attributes["transition"] == kind.value


def test_event_contains_stream_health_identity():
    factory = StreamingHealthTransitionEventFactory()

    event = factory.create(
        transition=transition(
            HealthStatus.HEALTHY,
            HealthStatus.CRITICAL,
            HealthTransitionKind.DEGRADED,
        ),
        source=NodeInstanceId("streaming-primary"),
        timestamp=TIMESTAMP,
    )

    assert event.source == NodeInstanceId(
        "streaming-primary"
    )
    assert "HEALTHY" in event.description
    assert "CRITICAL" in event.description
    assert "CRITICAL" in event.title


def test_event_id_is_unique_per_creation():
    factory = StreamingHealthTransitionEventFactory()

    value = transition(
        HealthStatus.HEALTHY,
        HealthStatus.DEGRADED,
        HealthTransitionKind.DEGRADED,
    )

    first = factory.create(
        transition=value,
        source=NodeInstanceId("streaming-primary"),
        timestamp=TIMESTAMP,
    )

    second = factory.create(
        transition=value,
        source=NodeInstanceId("streaming-primary"),
        timestamp=TIMESTAMP,
    )

    assert first.event_id
    assert second.event_id
    assert first.event_id != second.event_id


def test_factory_rejects_invalid_transition():
    factory = StreamingHealthTransitionEventFactory()

    with pytest.raises(
        TypeError,
        match="transition must be a StreamingHealthTransition",
    ):
        factory.create(
            transition=object(),  # type: ignore[arg-type]
            source=NodeInstanceId("streaming-primary"),
            timestamp=TIMESTAMP,
        )


def test_event_contains_single_srt_connection_cause():
    from app.domain.streaming.health import (
        SRTConnectionHealth,
        SRTPathHealth,
    )

    previous_connection = SRTConnectionHealth(
        connection_id="conn-ejtv",
        path_name="ejtv",
        state="read",
        rtt_ms=12.0,
        packets_retransmitted=100,
        packets_lost=100,
        status=HealthStatus.HEALTHY,
        message="Conexión SRT estable.",
        send_rate_mbps=4.0,
        link_capacity_mbps=100.0,
        link_utilization_percent=4.0,
        remote_address="203.0.113.25:9000",
        role="READER",
    )

    current_connection = SRTConnectionHealth(
        connection_id="conn-ejtv",
        path_name="ejtv",
        state="read",
        rtt_ms=12.5,
        packets_retransmitted=120,
        packets_lost=120,
        status=HealthStatus.DEGRADED,
        message="Conexión SRT degradada.",
        send_rate_mbps=4.0,
        link_capacity_mbps=100.0,
        link_utilization_percent=4.0,
        remote_address="203.0.113.25:9000",
        role="READER",
    )

    previous_path = SRTPathHealth(
        name="ejtv",
        connections=(previous_connection,),
        average_rtt_ms=12.0,
        total_packets_retransmitted=100,
        total_packets_lost=100,
        status=HealthStatus.HEALTHY,
        message="Path SRT estable.",
        maximum_rtt_ms=12.0,
        average_link_utilization_percent=4.0,
    )

    current_path = SRTPathHealth(
        name="ejtv",
        connections=(current_connection,),
        average_rtt_ms=12.5,
        total_packets_retransmitted=120,
        total_packets_lost=120,
        status=HealthStatus.DEGRADED,
        message="Path SRT degradado.",
        maximum_rtt_ms=12.5,
        average_link_utilization_percent=4.0,
    )

    previous_health = StreamingHealth(
        captured_at=TIMESTAMP,
        paths=(previous_path,),
        status=HealthStatus.HEALTHY,
        message="Streaming SRT estable.",
    )

    current_health = StreamingHealth(
        captured_at=TIMESTAMP,
        paths=(current_path,),
        status=HealthStatus.DEGRADED,
        message="Streaming SRT degradado.",
    )

    value = StreamingHealthTransition(
        previous=previous_health,
        current=current_health,
        kind=HealthTransitionKind.DEGRADED,
    )

    event = StreamingHealthTransitionEventFactory().create(
        transition=value,
        source=NodeInstanceId("streaming-primary"),
        timestamp=TIMESTAMP,
    )

    assert event.attributes is not None

    assert event.attributes["previous"] == "HEALTHY"
    assert event.attributes["current"] == "DEGRADED"
    assert event.attributes["transition"] == "DEGRADED"

    assert event.attributes["protocol"] == "SRT"
    assert event.attributes["path"] == "ejtv"
    assert event.attributes["connection_id"] == "conn-ejtv"
    assert event.attributes["connection_state"] == "read"
    assert event.attributes["cause_previous"] == "HEALTHY"
    assert event.attributes["cause_current"] == "DEGRADED"
    assert event.attributes["remote_address"] == "203.0.113.25:9000"
    assert event.attributes["role"] == "READER"


def test_event_does_not_attribute_multiple_srt_connection_causes_to_one():
    from app.domain.streaming.health import (
        SRTConnectionHealth,
        SRTPathHealth,
    )

    def connection(
        *,
        connection_id,
        path_name,
        status,
    ):
        return SRTConnectionHealth(
            connection_id=connection_id,
            path_name=path_name,
            state="read",
            rtt_ms=10.0,
            packets_retransmitted=100,
            packets_lost=100,
            status=status,
            message=f"Connection {status.value}",
            send_rate_mbps=4.0,
            link_capacity_mbps=100.0,
            link_utilization_percent=4.0,
        )

    previous_ejtv = connection(
        connection_id="conn-ejtv",
        path_name="ejtv",
        status=HealthStatus.HEALTHY,
    )
    current_ejtv = connection(
        connection_id="conn-ejtv",
        path_name="ejtv",
        status=HealthStatus.DEGRADED,
    )

    previous_enlace = connection(
        connection_id="conn-enlace",
        path_name="enlace",
        status=HealthStatus.HEALTHY,
    )
    current_enlace = connection(
        connection_id="conn-enlace",
        path_name="enlace",
        status=HealthStatus.CRITICAL,
    )

    previous_health = StreamingHealth(
        captured_at=TIMESTAMP,
        paths=(
            SRTPathHealth(
                name="ejtv",
                connections=(previous_ejtv,),
                average_rtt_ms=10.0,
                total_packets_retransmitted=100,
                total_packets_lost=100,
                status=HealthStatus.HEALTHY,
                message="Path SRT estable.",
                maximum_rtt_ms=10.0,
                average_link_utilization_percent=4.0,
            ),
            SRTPathHealth(
                name="enlace",
                connections=(previous_enlace,),
                average_rtt_ms=10.0,
                total_packets_retransmitted=100,
                total_packets_lost=100,
                status=HealthStatus.HEALTHY,
                message="Path SRT estable.",
                maximum_rtt_ms=10.0,
                average_link_utilization_percent=4.0,
            ),
        ),
        status=HealthStatus.HEALTHY,
        message="Streaming SRT estable.",
    )

    current_health = StreamingHealth(
        captured_at=TIMESTAMP,
        paths=(
            SRTPathHealth(
                name="ejtv",
                connections=(current_ejtv,),
                average_rtt_ms=10.0,
                total_packets_retransmitted=100,
                total_packets_lost=100,
                status=HealthStatus.DEGRADED,
                message="Path SRT degradado.",
                maximum_rtt_ms=10.0,
                average_link_utilization_percent=4.0,
            ),
            SRTPathHealth(
                name="enlace",
                connections=(current_enlace,),
                average_rtt_ms=10.0,
                total_packets_retransmitted=100,
                total_packets_lost=100,
                status=HealthStatus.CRITICAL,
                message="Path SRT crítico.",
                maximum_rtt_ms=10.0,
                average_link_utilization_percent=4.0,
            ),
        ),
        status=HealthStatus.CRITICAL,
        message="Streaming SRT requiere atención.",
    )

    value = StreamingHealthTransition(
        previous=previous_health,
        current=current_health,
        kind=HealthTransitionKind.DEGRADED,
    )

    event = StreamingHealthTransitionEventFactory().create(
        transition=value,
        source=NodeInstanceId("streaming-primary"),
        timestamp=TIMESTAMP,
    )

    assert event.attributes is not None

    # Global transition remains durable.
    assert event.attributes["previous"] == "HEALTHY"
    assert event.attributes["current"] == "CRITICAL"
    assert event.attributes["transition"] == "DEGRADED"

    # Two causal connections exist. The event must not lie by selecting one.
    assert "path" not in event.attributes
    assert "connection_id" not in event.attributes
    assert "connection_state" not in event.attributes
    assert "cause_previous" not in event.attributes
    assert "cause_current" not in event.attributes

    # Protocol is also omitted for this v1 causal contract because
    # protocol/path are emitted together only for one attributable cause.
    assert "protocol" not in event.attributes


def test_recovered_event_contains_single_srt_connection_cause():
    from app.domain.streaming.health import (
        SRTConnectionHealth,
        SRTPathHealth,
    )

    def connection(
        *,
        connection_id,
        path_name,
        status,
    ):
        return SRTConnectionHealth(
            connection_id=connection_id,
            path_name=path_name,
            state="read",
            rtt_ms=10.0,
            packets_retransmitted=100,
            packets_lost=100,
            status=status,
            message=f"Connection {status.value}",
            send_rate_mbps=4.0,
            link_capacity_mbps=100.0,
            link_utilization_percent=4.0,
        )

    previous_ejtv = connection(
        connection_id="conn-ejtv",
        path_name="ejtv",
        status=HealthStatus.CRITICAL,
    )

    current_ejtv = connection(
        connection_id="conn-ejtv",
        path_name="ejtv",
        status=HealthStatus.HEALTHY,
    )

    previous_enlace = connection(
        connection_id="conn-enlace",
        path_name="enlace",
        status=HealthStatus.HEALTHY,
    )

    current_enlace = connection(
        connection_id="conn-enlace",
        path_name="enlace",
        status=HealthStatus.HEALTHY,
    )

    previous_health = StreamingHealth(
        captured_at=TIMESTAMP,
        paths=(
            SRTPathHealth(
                name="ejtv",
                connections=(previous_ejtv,),
                average_rtt_ms=10.0,
                total_packets_retransmitted=100,
                total_packets_lost=100,
                status=HealthStatus.CRITICAL,
                message="Path SRT crítico.",
                maximum_rtt_ms=10.0,
                average_link_utilization_percent=4.0,
            ),
            SRTPathHealth(
                name="enlace",
                connections=(previous_enlace,),
                average_rtt_ms=10.0,
                total_packets_retransmitted=100,
                total_packets_lost=100,
                status=HealthStatus.HEALTHY,
                message="Path SRT estable.",
                maximum_rtt_ms=10.0,
                average_link_utilization_percent=4.0,
            ),
        ),
        status=HealthStatus.CRITICAL,
        message="Streaming SRT requiere atención.",
    )

    current_health = StreamingHealth(
        captured_at=TIMESTAMP,
        paths=(
            SRTPathHealth(
                name="ejtv",
                connections=(current_ejtv,),
                average_rtt_ms=10.0,
                total_packets_retransmitted=100,
                total_packets_lost=100,
                status=HealthStatus.HEALTHY,
                message="Path SRT estable.",
                maximum_rtt_ms=10.0,
                average_link_utilization_percent=4.0,
            ),
            SRTPathHealth(
                name="enlace",
                connections=(current_enlace,),
                average_rtt_ms=10.0,
                total_packets_retransmitted=100,
                total_packets_lost=100,
                status=HealthStatus.HEALTHY,
                message="Path SRT estable.",
                maximum_rtt_ms=10.0,
                average_link_utilization_percent=4.0,
            ),
        ),
        status=HealthStatus.HEALTHY,
        message="Streaming SRT estable.",
    )

    value = StreamingHealthTransition(
        previous=previous_health,
        current=current_health,
        kind=HealthTransitionKind.RECOVERED,
    )

    event = StreamingHealthTransitionEventFactory().create(
        transition=value,
        source=NodeInstanceId("streaming-primary"),
        timestamp=TIMESTAMP,
    )

    assert event.event_type == "STREAM_HEALTH_RECOVERED"

    assert event.attributes is not None

    assert event.attributes["previous"] == "CRITICAL"
    assert event.attributes["current"] == "HEALTHY"
    assert event.attributes["transition"] == "RECOVERED"

    assert event.attributes["protocol"] == "SRT"
    assert event.attributes["path"] == "ejtv"
    assert event.attributes["connection_id"] == "conn-ejtv"
    assert event.attributes["connection_state"] == "read"
    assert event.attributes["cause_previous"] == "CRITICAL"
    assert event.attributes["cause_current"] == "HEALTHY"
