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
