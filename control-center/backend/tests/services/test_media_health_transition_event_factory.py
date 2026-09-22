"""Tests for MediaHealth transition -> EventRecord mapping.

ENG-013C — Media Health -> NOC integration

This contract maps one already-detected MediaHealthTransition to an
operational EventRecord.

The factory does not:

- evaluate Media Health;
- stabilize Media Health;
- detect transitions;
- persist events;
- create or manage alarms.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.domain.streaming.health import HealthStatus
from app.domain.streaming.media_health import MediaHealth
from app.noc.domain.node_event import EventSeverity
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.services.health_transition_detector import (
    HealthTransitionKind,
)
from app.services.media_health_transition_detector import (
    MediaHealthTransition,
)
from app.services.media_health_transition_event_factory import (
    MediaHealthTransitionEventFactory,
)


TIMESTAMP = datetime(
    2026,
    9,
    22,
    18,
    30,
    tzinfo=UTC,
)


def health(
    status: HealthStatus,
    *,
    profile_id: str = "impact-main",
    service_id: str = "impact",
    path_name: str | None = "impact",
) -> MediaHealth:
    return MediaHealth(
        profile_id=profile_id,
        service_id=service_id,
        path_name=path_name,
        status=status,
        container=None,
        video=None,
        audio=None,
    )


def transition(
    previous: HealthStatus,
    current: HealthStatus,
    kind: HealthTransitionKind,
    *,
    path_name: str | None = "impact",
) -> MediaHealthTransition:
    return MediaHealthTransition(
        previous=health(
            previous,
            path_name=path_name,
        ),
        current=health(
            current,
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
            "MEDIA_HEALTH_DEGRADED",
            EventSeverity.WARNING,
        ),
        (
            HealthStatus.HEALTHY,
            HealthStatus.CRITICAL,
            HealthTransitionKind.DEGRADED,
            "MEDIA_HEALTH_DEGRADED",
            EventSeverity.CRITICAL,
        ),
        (
            HealthStatus.CRITICAL,
            HealthStatus.DEGRADED,
            HealthTransitionKind.IMPROVED,
            "MEDIA_HEALTH_IMPROVED",
            EventSeverity.NOTICE,
        ),
        (
            HealthStatus.DEGRADED,
            HealthStatus.HEALTHY,
            HealthTransitionKind.RECOVERED,
            "MEDIA_HEALTH_RECOVERED",
            EventSeverity.INFO,
        ),
        (
            HealthStatus.HEALTHY,
            HealthStatus.UNKNOWN,
            HealthTransitionKind.UNKNOWN,
            "MEDIA_HEALTH_UNKNOWN",
            EventSeverity.NOTICE,
        ),
        (
            HealthStatus.UNKNOWN,
            HealthStatus.HEALTHY,
            HealthTransitionKind.UNKNOWN,
            "MEDIA_HEALTH_UNKNOWN",
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
    factory = MediaHealthTransitionEventFactory()

    event = factory.create(
        transition=transition(
            previous,
            current,
            kind,
        ),
        source=NodeInstanceId(
            "streaming-primary"
        ),
        timestamp=TIMESTAMP,
    )

    assert event.event_type == event_type
    assert event.severity is severity

    assert event.attributes is not None
    assert event.attributes["previous"] == previous.value
    assert event.attributes["current"] == current.value
    assert event.attributes["transition"] == kind.value


def test_event_preserves_media_profile_identity() -> None:
    factory = MediaHealthTransitionEventFactory()

    value = transition(
        HealthStatus.HEALTHY,
        HealthStatus.DEGRADED,
        HealthTransitionKind.DEGRADED,
    )

    event = factory.create(
        transition=value,
        source=NodeInstanceId(
            "streaming-primary"
        ),
        timestamp=TIMESTAMP,
    )

    assert event.source == NodeInstanceId(
        "streaming-primary"
    )

    assert event.attributes is not None
    assert event.attributes["profile_id"] == "impact-main"
    assert event.attributes["service_id"] == "impact"
    assert event.attributes["path_name"] == "impact"


def test_event_preserves_none_path_name() -> None:
    factory = MediaHealthTransitionEventFactory()

    value = transition(
        HealthStatus.HEALTHY,
        HealthStatus.DEGRADED,
        HealthTransitionKind.DEGRADED,
        path_name=None,
    )

    event = factory.create(
        transition=value,
        source=NodeInstanceId(
            "streaming-primary"
        ),
        timestamp=TIMESTAMP,
    )

    assert event.attributes is not None
    assert "path_name" not in event.attributes


def test_title_and_description_identify_media_profile() -> None:
    factory = MediaHealthTransitionEventFactory()

    event = factory.create(
        transition=transition(
            HealthStatus.HEALTHY,
            HealthStatus.DEGRADED,
            HealthTransitionKind.DEGRADED,
        ),
        source=NodeInstanceId(
            "streaming-primary"
        ),
        timestamp=TIMESTAMP,
    )

    assert "impact-main" in event.title
    assert "impact-main" in event.description
    assert "HEALTHY" in event.description
    assert "DEGRADED" in event.description


def test_event_id_is_unique_per_creation() -> None:
    factory = MediaHealthTransitionEventFactory()

    value = transition(
        HealthStatus.HEALTHY,
        HealthStatus.DEGRADED,
        HealthTransitionKind.DEGRADED,
    )

    first = factory.create(
        transition=value,
        source=NodeInstanceId(
            "streaming-primary"
        ),
        timestamp=TIMESTAMP,
    )

    second = factory.create(
        transition=value,
        source=NodeInstanceId(
            "streaming-primary"
        ),
        timestamp=TIMESTAMP,
    )

    assert first.event_id
    assert second.event_id
    assert first.event_id != second.event_id


def test_factory_rejects_invalid_transition() -> None:
    factory = MediaHealthTransitionEventFactory()

    with pytest.raises(
        TypeError,
        match="transition must be a MediaHealthTransition",
    ):
        factory.create(
            transition=object(),  # type: ignore[arg-type]
            source=NodeInstanceId(
                "streaming-primary"
            ),
            timestamp=TIMESTAMP,
        )


def test_factory_rejects_invalid_source() -> None:
    factory = MediaHealthTransitionEventFactory()

    with pytest.raises(
        TypeError,
        match="source must be a NodeInstanceId",
    ):
        factory.create(
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
            22,
            18,
            30,
        ),
    ),
)
def test_factory_rejects_invalid_timestamp(
    timestamp,
) -> None:
    factory = MediaHealthTransitionEventFactory()

    expected_exception = (
        TypeError
        if isinstance(timestamp, str)
        else ValueError
    )

    with pytest.raises(expected_exception):
        factory.create(
            transition=transition(
                HealthStatus.HEALTHY,
                HealthStatus.DEGRADED,
                HealthTransitionKind.DEGRADED,
            ),
            source=NodeInstanceId(
                "streaming-primary"
            ),
            timestamp=timestamp,
        )
