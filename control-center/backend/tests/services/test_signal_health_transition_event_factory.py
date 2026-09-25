"""Tests for SignalHealth transition -> EventRecord mapping.

ENG-013C — Signal Health -> NOC integration

This contract maps one already-detected SignalHealthTransition to one
operational EventRecord.

The factory does not:

- evaluate Signal Health;
- evaluate Media Health;
- evaluate Source Transport Health;
- detect transitions;
- capture MediaMTX;
- persist events;
- create or manage alarms.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.domain.streaming.health import HealthStatus
from app.domain.streaming.signal_health import SignalHealth
from app.noc.domain.node_event import EventSeverity
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.services.health_transition_detector import (
    HealthTransitionKind,
)
from app.services.signal_health_transition_detector import (
    SignalHealthTransition,
)
from app.services.signal_health_transition_event_factory import (
    SignalHealthTransitionEventFactory,
)


TIMESTAMP = datetime(
    2026,
    9,
    24,
    18,
    30,
    tzinfo=UTC,
)


def health(
    status: HealthStatus,
    *,
    media_status: HealthStatus = HealthStatus.HEALTHY,
    transport_status: HealthStatus = HealthStatus.HEALTHY,
    profile_id: str = "impact-main",
    service_id: str = "impact",
    path_name: str | None = "impact",
) -> SignalHealth:
    return SignalHealth(
        profile_id=profile_id,
        service_id=service_id,
        path_name=path_name,
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
    path_name: str | None = "impact",
) -> SignalHealthTransition:
    return SignalHealthTransition(
        previous=health(
            previous,
            media_status=previous_media,
            transport_status=previous_transport,
            path_name=path_name,
        ),
        current=health(
            current,
            media_status=current_media,
            transport_status=current_transport,
            path_name=path_name,
        ),
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
            "SIGNAL_HEALTH_DEGRADED",
            EventSeverity.WARNING,
        ),
        (
            HealthStatus.HEALTHY,
            HealthStatus.CRITICAL,
            HealthTransitionKind.DEGRADED,
            "SIGNAL_HEALTH_DEGRADED",
            EventSeverity.CRITICAL,
        ),
        (
            HealthStatus.DEGRADED,
            HealthStatus.CRITICAL,
            HealthTransitionKind.DEGRADED,
            "SIGNAL_HEALTH_DEGRADED",
            EventSeverity.CRITICAL,
        ),
        (
            HealthStatus.CRITICAL,
            HealthStatus.DEGRADED,
            HealthTransitionKind.IMPROVED,
            "SIGNAL_HEALTH_IMPROVED",
            EventSeverity.NOTICE,
        ),
        (
            HealthStatus.DEGRADED,
            HealthStatus.HEALTHY,
            HealthTransitionKind.RECOVERED,
            "SIGNAL_HEALTH_RECOVERED",
            EventSeverity.INFO,
        ),
        (
            HealthStatus.CRITICAL,
            HealthStatus.HEALTHY,
            HealthTransitionKind.RECOVERED,
            "SIGNAL_HEALTH_RECOVERED",
            EventSeverity.INFO,
        ),
        (
            HealthStatus.HEALTHY,
            HealthStatus.UNKNOWN,
            HealthTransitionKind.UNKNOWN,
            "SIGNAL_HEALTH_UNKNOWN",
            EventSeverity.NOTICE,
        ),
        (
            HealthStatus.UNKNOWN,
            HealthStatus.HEALTHY,
            HealthTransitionKind.UNKNOWN,
            "SIGNAL_HEALTH_UNKNOWN",
            EventSeverity.NOTICE,
        ),
        (
            HealthStatus.UNKNOWN,
            HealthStatus.DEGRADED,
            HealthTransitionKind.UNKNOWN,
            "SIGNAL_HEALTH_UNKNOWN",
            EventSeverity.NOTICE,
        ),
        (
            HealthStatus.UNKNOWN,
            HealthStatus.CRITICAL,
            HealthTransitionKind.UNKNOWN,
            "SIGNAL_HEALTH_UNKNOWN",
            EventSeverity.NOTICE,
        ),
    ),
)
def test_factory_maps_transition_to_event(
    previous: HealthStatus,
    current: HealthStatus,
    kind: HealthTransitionKind,
    event_type: str,
    severity: EventSeverity,
) -> None:
    event = SignalHealthTransitionEventFactory().create(
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


def test_event_preserves_signal_identity() -> None:
    event = SignalHealthTransitionEventFactory().create(
        transition=transition(
            HealthStatus.HEALTHY,
            HealthStatus.DEGRADED,
            HealthTransitionKind.DEGRADED,
        ),
        source=NodeInstanceId("streaming-primary"),
        timestamp=TIMESTAMP,
    )

    assert event.source == NodeInstanceId(
        "streaming-primary"
    )

    assert event.attributes is not None
    assert event.attributes["profile_id"] == "impact-main"
    assert event.attributes["service_id"] == "impact"
    assert event.attributes["path_name"] == "impact"


def test_event_preserves_component_conclusions() -> None:
    event = SignalHealthTransitionEventFactory().create(
        transition=transition(
            HealthStatus.DEGRADED,
            HealthStatus.CRITICAL,
            HealthTransitionKind.DEGRADED,
            previous_media=HealthStatus.HEALTHY,
            current_media=HealthStatus.CRITICAL,
            previous_transport=HealthStatus.DEGRADED,
            current_transport=HealthStatus.DEGRADED,
        ),
        source=NodeInstanceId("streaming-primary"),
        timestamp=TIMESTAMP,
    )

    assert event.attributes is not None

    assert event.attributes["media_previous"] == "HEALTHY"
    assert event.attributes["media_current"] == "CRITICAL"

    assert (
        event.attributes["transport_previous"]
        == "DEGRADED"
    )
    assert (
        event.attributes["transport_current"]
        == "DEGRADED"
    )


def test_event_preserves_none_path_name() -> None:
    event = SignalHealthTransitionEventFactory().create(
        transition=transition(
            HealthStatus.HEALTHY,
            HealthStatus.DEGRADED,
            HealthTransitionKind.DEGRADED,
            path_name=None,
        ),
        source=NodeInstanceId("streaming-primary"),
        timestamp=TIMESTAMP,
    )

    assert event.attributes is not None
    assert "path_name" not in event.attributes


def test_title_and_description_identify_signal_profile() -> None:
    event = SignalHealthTransitionEventFactory().create(
        transition=transition(
            HealthStatus.HEALTHY,
            HealthStatus.DEGRADED,
            HealthTransitionKind.DEGRADED,
        ),
        source=NodeInstanceId("streaming-primary"),
        timestamp=TIMESTAMP,
    )

    assert "impact-main" in event.title
    assert "impact-main" in event.description
    assert "HEALTHY" in event.description
    assert "DEGRADED" in event.description


def test_event_id_is_unique_per_creation() -> None:
    value = transition(
        HealthStatus.HEALTHY,
        HealthStatus.DEGRADED,
        HealthTransitionKind.DEGRADED,
    )

    factory = SignalHealthTransitionEventFactory()

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


def test_factory_rejects_invalid_transition() -> None:
    with pytest.raises(
        TypeError,
        match="transition must be a SignalHealthTransition",
    ):
        SignalHealthTransitionEventFactory().create(
            transition=object(),  # type: ignore[arg-type]
            source=NodeInstanceId("streaming-primary"),
            timestamp=TIMESTAMP,
        )


def test_factory_rejects_invalid_source() -> None:
    with pytest.raises(
        TypeError,
        match="source must be a NodeInstanceId",
    ):
        SignalHealthTransitionEventFactory().create(
            transition=transition(
                HealthStatus.HEALTHY,
                HealthStatus.DEGRADED,
                HealthTransitionKind.DEGRADED,
            ),
            source="streaming-primary",  # type: ignore[arg-type]
            timestamp=TIMESTAMP,
        )


@pytest.mark.parametrize(
    "timestamp",
    (
        "invalid",
        datetime(
            2026,
            9,
            24,
            18,
            30,
        ),
    ),
)
def test_factory_rejects_invalid_timestamp(
    timestamp,
) -> None:
    expected_exception = (
        TypeError
        if isinstance(timestamp, str)
        else ValueError
    )

    with pytest.raises(expected_exception):
        SignalHealthTransitionEventFactory().create(
            transition=transition(
                HealthStatus.HEALTHY,
                HealthStatus.DEGRADED,
                HealthTransitionKind.DEGRADED,
            ),
            source=NodeInstanceId("streaming-primary"),
            timestamp=timestamp,
        )
