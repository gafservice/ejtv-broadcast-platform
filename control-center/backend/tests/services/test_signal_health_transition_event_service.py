"""Tests for SignalHealth transition event coordination.

ENG-013C — Signal Health -> NOC integration

The service coordinates an already-detected SignalHealthTransition
with the existing EventService.

It does not:

- evaluate Signal Health;
- evaluate Media Health;
- evaluate Source Transport Health;
- detect transitions;
- capture MediaMTX state;
- own persistence;
- create or manage alarms.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.domain.streaming.health import HealthStatus
from app.domain.streaming.signal_health import SignalHealth
from app.noc.domain.node import Node
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.domain.node_type import NodeType
from app.noc.infrastructure.memory_repository import (
    InMemoryNodeRepository,
)
from app.noc.registry.registry import NodeRegistry
from app.noc.services.event_service import (
    EventDisposition,
    EventService,
)
from app.noc.services.health_transition_detector import (
    HealthTransitionKind,
)
from app.services.signal_health_transition_detector import (
    SignalHealthTransition,
)
from app.services.signal_health_transition_event_factory import (
    SignalHealthTransitionEventFactory,
)
from app.services.signal_health_transition_event_service import (
    SignalHealthTransitionEventResult,
    SignalHealthTransitionEventService,
)


TIMESTAMP = datetime(
    2026,
    9,
    24,
    19,
    30,
    tzinfo=UTC,
)


def build_context():
    repository = InMemoryNodeRepository()
    registry = NodeRegistry(repository)

    node = Node(
        node_id=NodeId.create(
            id="streaming-core",
            name="streaming-core",
            display_name="Streaming Core",
        ),
        node_type=NodeType.STREAMING,
    )

    instance = node.create_instance(
        instance_id="streaming-primary"
    )

    registry.register(node)

    event_service = EventService(registry)

    service = SignalHealthTransitionEventService(
        event_service=event_service,
    )

    return (
        node,
        instance,
        event_service,
        service,
    )


def health(
    status: HealthStatus,
    *,
    media_status: HealthStatus = HealthStatus.HEALTHY,
    transport_status: HealthStatus = HealthStatus.HEALTHY,
) -> SignalHealth:
    return SignalHealth(
        profile_id="impact-main",
        service_id="impact",
        path_name="impact",
        media_status=media_status,
        transport_status=transport_status,
        status=status,
    )


def transition(
    previous: HealthStatus,
    current: HealthStatus,
    kind: HealthTransitionKind,
    *,
    previous_media: HealthStatus = HealthStatus.HEALTHY,
    current_media: HealthStatus = HealthStatus.HEALTHY,
    previous_transport: HealthStatus = HealthStatus.HEALTHY,
    current_transport: HealthStatus = HealthStatus.HEALTHY,
) -> SignalHealthTransition:
    return SignalHealthTransition(
        previous=health(
            previous,
            media_status=previous_media,
            transport_status=previous_transport,
        ),
        current=health(
            current,
            media_status=current_media,
            transport_status=current_transport,
        ),
        kind=kind,
    )


def test_constructor_builds_default_factory():
    _, _, event_service, service = build_context()

    assert service.event_service is event_service
    assert isinstance(
        service.factory,
        SignalHealthTransitionEventFactory,
    )


def test_process_transition_persists_one_event():
    node, instance, event_service, service = build_context()

    value = transition(
        HealthStatus.HEALTHY,
        HealthStatus.DEGRADED,
        HealthTransitionKind.DEGRADED,
        previous_media=HealthStatus.HEALTHY,
        current_media=HealthStatus.DEGRADED,
    )

    result = service.process_transition(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        transition=value,
        timestamp=TIMESTAMP,
    )

    assert isinstance(
        result,
        SignalHealthTransitionEventResult,
    )

    assert result.transition is value
    assert result.event is not None
    assert result.receipt is not None

    assert (
        result.event.event_type
        == "SIGNAL_HEALTH_DEGRADED"
    )

    assert (
        result.receipt.disposition
        is EventDisposition.RECORDED
    )

    assert result.receipt.event is result.event

    events = event_service.list_all(
        node.node_id,
        instance.instance_id,
    )

    assert events == (result.event,)


def test_process_none_transition_persists_nothing():
    node, instance, event_service, service = build_context()

    result = service.process_transition(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        transition=None,
        timestamp=TIMESTAMP,
    )

    assert result.transition is None
    assert result.event is None
    assert result.receipt is None

    assert event_service.list_all(
        node.node_id,
        instance.instance_id,
    ) == ()


def test_multiple_calls_append_multiple_events():
    node, instance, event_service, service = build_context()

    first = service.process_transition(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        transition=transition(
            HealthStatus.HEALTHY,
            HealthStatus.DEGRADED,
            HealthTransitionKind.DEGRADED,
        ),
        timestamp=TIMESTAMP,
    )

    second = service.process_transition(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        transition=transition(
            HealthStatus.DEGRADED,
            HealthStatus.HEALTHY,
            HealthTransitionKind.RECOVERED,
        ),
        timestamp=TIMESTAMP,
    )

    assert first.event is not None
    assert second.event is not None

    assert first.event.event_id != second.event.event_id

    events = event_service.list_all(
        node.node_id,
        instance.instance_id,
    )

    assert len(events) == 2

    assert (
        events[0].event_type
        == "SIGNAL_HEALTH_DEGRADED"
    )

    assert (
        events[1].event_type
        == "SIGNAL_HEALTH_RECOVERED"
    )


def test_service_preserves_component_attributes():
    node, instance, _, service = build_context()

    result = service.process_transition(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        transition=transition(
            HealthStatus.DEGRADED,
            HealthStatus.CRITICAL,
            HealthTransitionKind.DEGRADED,
            previous_media=HealthStatus.HEALTHY,
            current_media=HealthStatus.CRITICAL,
            previous_transport=HealthStatus.DEGRADED,
            current_transport=HealthStatus.DEGRADED,
        ),
        timestamp=TIMESTAMP,
    )

    assert result.event is not None
    assert result.event.attributes is not None

    assert (
        result.event.attributes["media_previous"]
        == "HEALTHY"
    )
    assert (
        result.event.attributes["media_current"]
        == "CRITICAL"
    )
    assert (
        result.event.attributes["transport_previous"]
        == "DEGRADED"
    )
    assert (
        result.event.attributes["transport_current"]
        == "DEGRADED"
    )


@pytest.mark.parametrize(
    (
        "field_name",
        "value",
        "expected_message",
    ),
    (
        (
            "node_id",
            object(),
            "node_id must be a NodeId",
        ),
        (
            "instance_id",
            "streaming-primary",
            "instance_id must be a NodeInstanceId",
        ),
        (
            "transition",
            object(),
            (
                "transition must be a "
                "SignalHealthTransition or None"
            ),
        ),
        (
            "timestamp",
            "invalid",
            "timestamp must be a datetime",
        ),
    ),
)
def test_process_transition_rejects_invalid_arguments(
    field_name,
    value,
    expected_message,
):
    node, instance, _, service = build_context()

    arguments = {
        "node_id": node.node_id,
        "instance_id": instance.instance_id,
        "transition": None,
        "timestamp": TIMESTAMP,
    }

    arguments[field_name] = value

    with pytest.raises(
        TypeError,
        match=expected_message,
    ):
        service.process_transition(
            **arguments,
        )


def test_process_transition_rejects_naive_timestamp():
    node, instance, _, service = build_context()

    with pytest.raises(
        ValueError,
        match="timestamp must be timezone-aware",
    ):
        service.process_transition(
            node_id=node.node_id,
            instance_id=instance.instance_id,
            transition=None,
            timestamp=datetime(
                2026,
                9,
                24,
                19,
                30,
            ),
        )


def test_constructor_rejects_invalid_event_service():
    with pytest.raises(
        TypeError,
        match="event_service must be an EventService",
    ):
        SignalHealthTransitionEventService(
            event_service=object(),
        )


def test_constructor_rejects_invalid_factory():
    _, _, event_service, _ = build_context()

    with pytest.raises(
        TypeError,
        match=(
            "factory must be a "
            "SignalHealthTransitionEventFactory or None"
        ),
    ):
        SignalHealthTransitionEventService(
            event_service=event_service,
            factory=object(),
        )
