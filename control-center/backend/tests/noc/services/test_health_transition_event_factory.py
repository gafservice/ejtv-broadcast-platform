from datetime import datetime, timezone

import pytest

from app.noc.domain.node_event import (
    EventRecord,
    EventSeverity,
)
from app.noc.domain.node_health import (
    NodeHealth,
    NodeHealthState,
)
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.services.health_transition_detector import (
    HealthTransition,
    HealthTransitionKind,
)
from app.noc.services.health_transition_event_factory import (
    HealthTransitionEventFactory,
)


BASE_TIME = datetime(
    2026,
    8,
    20,
    21,
    0,
    tzinfo=timezone.utc,
)


def make_transition(
    *,
    previous: NodeHealthState,
    current: NodeHealthState,
    kind: HealthTransitionKind,
) -> HealthTransition:
    return HealthTransition(
        previous=NodeHealth(previous),
        current=NodeHealth(current),
        kind=kind,
    )


def test_factory_requires_transition():
    factory = HealthTransitionEventFactory()

    with pytest.raises(TypeError):
        factory.create(
            transition=object(),  # type: ignore[arg-type]
            source=NodeInstanceId("streaming-primary"),
            timestamp=BASE_TIME,
        )


def test_factory_requires_source():
    factory = HealthTransitionEventFactory()

    transition = make_transition(
        previous=NodeHealthState.HEALTHY,
        current=NodeHealthState.WARNING,
        kind=HealthTransitionKind.DEGRADED,
    )

    with pytest.raises(TypeError):
        factory.create(
            transition=transition,
            source="streaming-primary",  # type: ignore[arg-type]
            timestamp=BASE_TIME,
        )


def test_factory_requires_datetime():
    factory = HealthTransitionEventFactory()

    transition = make_transition(
        previous=NodeHealthState.HEALTHY,
        current=NodeHealthState.WARNING,
        kind=HealthTransitionKind.DEGRADED,
    )

    with pytest.raises(TypeError):
        factory.create(
            transition=transition,
            source=NodeInstanceId("streaming-primary"),
            timestamp="2026-08-20T21:00:00Z",  # type: ignore[arg-type]
        )


def test_factory_requires_timezone_aware_timestamp():
    factory = HealthTransitionEventFactory()

    transition = make_transition(
        previous=NodeHealthState.HEALTHY,
        current=NodeHealthState.WARNING,
        kind=HealthTransitionKind.DEGRADED,
    )

    naive = datetime(
        2026,
        8,
        20,
        21,
        0,
    )

    with pytest.raises(ValueError):
        factory.create(
            transition=transition,
            source=NodeInstanceId("streaming-primary"),
            timestamp=naive,
        )


def test_factory_requires_utc_timestamp():
    factory = HealthTransitionEventFactory()

    transition = make_transition(
        previous=NodeHealthState.HEALTHY,
        current=NodeHealthState.WARNING,
        kind=HealthTransitionKind.DEGRADED,
    )

    non_utc = datetime(
        2026,
        8,
        20,
        21,
        0,
        tzinfo=timezone(
            __import__("datetime").timedelta(hours=-6)
        ),
    )

    with pytest.raises(ValueError):
        factory.create(
            transition=transition,
            source=NodeInstanceId("streaming-primary"),
            timestamp=non_utc,
        )


def test_warning_degradation_creates_warning_event():
    factory = HealthTransitionEventFactory()

    transition = make_transition(
        previous=NodeHealthState.HEALTHY,
        current=NodeHealthState.WARNING,
        kind=HealthTransitionKind.DEGRADED,
    )

    event = factory.create(
        transition=transition,
        source=NodeInstanceId("streaming-primary"),
        timestamp=BASE_TIME,
    )

    assert isinstance(event, EventRecord)
    assert event.event_type == "NODE_HEALTH_DEGRADED"
    assert event.severity is EventSeverity.WARNING
    assert event.source == NodeInstanceId("streaming-primary")
    assert event.timestamp == BASE_TIME


def test_degraded_state_creates_error_event():
    factory = HealthTransitionEventFactory()

    transition = make_transition(
        previous=NodeHealthState.WARNING,
        current=NodeHealthState.DEGRADED,
        kind=HealthTransitionKind.DEGRADED,
    )

    event = factory.create(
        transition=transition,
        source=NodeInstanceId("streaming-primary"),
        timestamp=BASE_TIME,
    )

    assert event.event_type == "NODE_HEALTH_DEGRADED"
    assert event.severity is EventSeverity.ERROR


def test_critical_state_creates_critical_event():
    factory = HealthTransitionEventFactory()

    transition = make_transition(
        previous=NodeHealthState.DEGRADED,
        current=NodeHealthState.CRITICAL,
        kind=HealthTransitionKind.DEGRADED,
    )

    event = factory.create(
        transition=transition,
        source=NodeInstanceId("streaming-primary"),
        timestamp=BASE_TIME,
    )

    assert event.event_type == "NODE_HEALTH_DEGRADED"
    assert event.severity is EventSeverity.CRITICAL


def test_improved_transition_creates_notice_event():
    factory = HealthTransitionEventFactory()

    transition = make_transition(
        previous=NodeHealthState.CRITICAL,
        current=NodeHealthState.DEGRADED,
        kind=HealthTransitionKind.IMPROVED,
    )

    event = factory.create(
        transition=transition,
        source=NodeInstanceId("streaming-primary"),
        timestamp=BASE_TIME,
    )

    assert event.event_type == "NODE_HEALTH_IMPROVED"
    assert event.severity is EventSeverity.NOTICE


def test_recovered_transition_creates_info_event():
    factory = HealthTransitionEventFactory()

    transition = make_transition(
        previous=NodeHealthState.WARNING,
        current=NodeHealthState.HEALTHY,
        kind=HealthTransitionKind.RECOVERED,
    )

    event = factory.create(
        transition=transition,
        source=NodeInstanceId("streaming-primary"),
        timestamp=BASE_TIME,
    )

    assert event.event_type == "NODE_HEALTH_RECOVERED"
    assert event.severity is EventSeverity.INFO


def test_unknown_transition_creates_notice_event():
    factory = HealthTransitionEventFactory()

    transition = make_transition(
        previous=NodeHealthState.HEALTHY,
        current=NodeHealthState.UNKNOWN,
        kind=HealthTransitionKind.UNKNOWN,
    )

    event = factory.create(
        transition=transition,
        source=NodeInstanceId("streaming-primary"),
        timestamp=BASE_TIME,
    )

    assert event.event_type == "NODE_HEALTH_UNKNOWN"
    assert event.severity is EventSeverity.NOTICE


def test_event_contains_transition_attributes():
    factory = HealthTransitionEventFactory()

    transition = make_transition(
        previous=NodeHealthState.HEALTHY,
        current=NodeHealthState.CRITICAL,
        kind=HealthTransitionKind.DEGRADED,
    )

    event = factory.create(
        transition=transition,
        source=NodeInstanceId("streaming-primary"),
        timestamp=BASE_TIME,
    )

    assert event.attributes is not None
    assert event.attributes["previous"] == "HEALTHY"
    assert event.attributes["current"] == "CRITICAL"
    assert event.attributes["transition"] == "DEGRADED"


def test_event_title_contains_current_state():
    factory = HealthTransitionEventFactory()

    transition = make_transition(
        previous=NodeHealthState.HEALTHY,
        current=NodeHealthState.CRITICAL,
        kind=HealthTransitionKind.DEGRADED,
    )

    event = factory.create(
        transition=transition,
        source=NodeInstanceId("streaming-primary"),
        timestamp=BASE_TIME,
    )

    assert "CRITICAL" in event.title


def test_event_description_contains_previous_and_current_state():
    factory = HealthTransitionEventFactory()

    transition = make_transition(
        previous=NodeHealthState.WARNING,
        current=NodeHealthState.HEALTHY,
        kind=HealthTransitionKind.RECOVERED,
    )

    event = factory.create(
        transition=transition,
        source=NodeInstanceId("streaming-primary"),
        timestamp=BASE_TIME,
    )

    assert "WARNING" in event.description
    assert "HEALTHY" in event.description


def test_event_id_is_not_empty():
    factory = HealthTransitionEventFactory()

    transition = make_transition(
        previous=NodeHealthState.HEALTHY,
        current=NodeHealthState.WARNING,
        kind=HealthTransitionKind.DEGRADED,
    )

    event = factory.create(
        transition=transition,
        source=NodeInstanceId("streaming-primary"),
        timestamp=BASE_TIME,
    )

    assert isinstance(event.event_id, str)
    assert event.event_id.strip()


def test_event_id_is_unique_per_creation():
    factory = HealthTransitionEventFactory()

    transition = make_transition(
        previous=NodeHealthState.HEALTHY,
        current=NodeHealthState.WARNING,
        kind=HealthTransitionKind.DEGRADED,
    )

    first = factory.create(
        transition=transition,
        source=NodeInstanceId("streaming-primary"),
        timestamp=BASE_TIME,
    )

    second = factory.create(
        transition=transition,
        source=NodeInstanceId("streaming-primary"),
        timestamp=BASE_TIME,
    )

    assert first.event_id != second.event_id
