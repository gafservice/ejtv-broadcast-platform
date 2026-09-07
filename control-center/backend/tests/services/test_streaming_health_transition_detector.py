from datetime import UTC, datetime

import pytest

from app.domain.streaming.health import (
    HealthStatus,
    StreamingHealth,
)
from app.noc.services.health_transition_detector import (
    HealthTransitionKind,
)
from app.services.streaming_health_transition_detector import (
    StreamingHealthTransition,
    StreamingHealthTransitionDetector,
)


CAPTURED_AT = datetime(2026, 9, 7, 0, 0, tzinfo=UTC)


def health(status: HealthStatus) -> StreamingHealth:
    return StreamingHealth(
        captured_at=CAPTURED_AT,
        paths=(),
        status=status,
        message=f"Streaming health: {status.value}",
    )


def test_first_observation_has_no_transition():
    detector = StreamingHealthTransitionDetector()

    result = detector.detect(
        None,
        health(HealthStatus.HEALTHY),
    )

    assert result is None


def test_same_status_has_no_transition():
    detector = StreamingHealthTransitionDetector()

    result = detector.detect(
        health(HealthStatus.HEALTHY),
        health(HealthStatus.HEALTHY),
    )

    assert result is None


@pytest.mark.parametrize(
    ("previous_status", "current_status"),
    [
        (HealthStatus.HEALTHY, HealthStatus.DEGRADED),
        (HealthStatus.HEALTHY, HealthStatus.CRITICAL),
        (HealthStatus.DEGRADED, HealthStatus.CRITICAL),
    ],
)
def test_worsening_known_health_is_degraded(
    previous_status: HealthStatus,
    current_status: HealthStatus,
):
    detector = StreamingHealthTransitionDetector()

    result = detector.detect(
        health(previous_status),
        health(current_status),
    )

    assert isinstance(result, StreamingHealthTransition)
    assert result.kind is HealthTransitionKind.DEGRADED
    assert result.previous.status is previous_status
    assert result.current.status is current_status


def test_critical_to_degraded_is_improved():
    detector = StreamingHealthTransitionDetector()

    result = detector.detect(
        health(HealthStatus.CRITICAL),
        health(HealthStatus.DEGRADED),
    )

    assert result is not None
    assert result.kind is HealthTransitionKind.IMPROVED


@pytest.mark.parametrize(
    "previous_status",
    [
        HealthStatus.DEGRADED,
        HealthStatus.CRITICAL,
    ],
)
def test_known_unhealthy_to_healthy_is_recovered(
    previous_status: HealthStatus,
):
    detector = StreamingHealthTransitionDetector()

    result = detector.detect(
        health(previous_status),
        health(HealthStatus.HEALTHY),
    )

    assert result is not None
    assert result.kind is HealthTransitionKind.RECOVERED


@pytest.mark.parametrize(
    "previous_status",
    [
        HealthStatus.HEALTHY,
        HealthStatus.DEGRADED,
        HealthStatus.CRITICAL,
    ],
)
def test_transition_to_unknown_is_unknown(
    previous_status: HealthStatus,
):
    detector = StreamingHealthTransitionDetector()

    result = detector.detect(
        health(previous_status),
        health(HealthStatus.UNKNOWN),
    )

    assert result is not None
    assert result.kind is HealthTransitionKind.UNKNOWN


@pytest.mark.parametrize(
    "current_status",
    [
        HealthStatus.HEALTHY,
        HealthStatus.DEGRADED,
        HealthStatus.CRITICAL,
    ],
)
def test_transition_from_unknown_is_unknown(
    current_status: HealthStatus,
):
    detector = StreamingHealthTransitionDetector()

    result = detector.detect(
        health(HealthStatus.UNKNOWN),
        health(current_status),
    )

    assert result is not None
    assert result.kind is HealthTransitionKind.UNKNOWN


def test_previous_requires_streaming_health_or_none():
    detector = StreamingHealthTransitionDetector()

    with pytest.raises(TypeError):
        detector.detect(
            object(),  # type: ignore[arg-type]
            health(HealthStatus.HEALTHY),
        )


def test_current_requires_streaming_health():
    detector = StreamingHealthTransitionDetector()

    with pytest.raises(TypeError):
        detector.detect(
            health(HealthStatus.HEALTHY),
            object(),  # type: ignore[arg-type]
        )


def test_transition_requires_streaming_health_values():
    with pytest.raises(TypeError):
        StreamingHealthTransition(
            previous=object(),  # type: ignore[arg-type]
            current=health(HealthStatus.DEGRADED),
            kind=HealthTransitionKind.DEGRADED,
        )


def test_transition_requires_transition_kind():
    with pytest.raises(TypeError):
        StreamingHealthTransition(
            previous=health(HealthStatus.HEALTHY),
            current=health(HealthStatus.DEGRADED),
            kind=object(),  # type: ignore[arg-type]
        )
