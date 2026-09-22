"""Tests for semantic transitions between stabilized MediaHealth values.

ENG-013C — Media Health -> NOC integration

These tests define only the transition-detection contract.

The detector:

- consumes stabilized MediaHealth values;
- preserves MediaHealth as previous/current evidence;
- reuses the canonical HealthTransitionKind vocabulary;
- does not evaluate or stabilize Media Health;
- does not create events or alarms;
- does not persist state.
"""

from __future__ import annotations

import pytest

from app.domain.streaming.health import HealthStatus
from app.domain.streaming.media_health import MediaHealth
from app.noc.services.health_transition_detector import HealthTransitionKind
from app.services.media_health_transition_detector import (
    MediaHealthTransition,
    MediaHealthTransitionDetector,
)


def _health(
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


def test_first_observation_does_not_create_transition() -> None:
    detector = MediaHealthTransitionDetector()

    current = _health(HealthStatus.HEALTHY)

    assert detector.detect(None, current) is None


def test_same_status_does_not_create_transition() -> None:
    detector = MediaHealthTransitionDetector()

    previous = _health(HealthStatus.HEALTHY)
    current = _health(HealthStatus.HEALTHY)

    assert detector.detect(previous, current) is None


def test_healthy_to_degraded_is_degraded_transition() -> None:
    detector = MediaHealthTransitionDetector()

    previous = _health(HealthStatus.HEALTHY)
    current = _health(HealthStatus.DEGRADED)

    transition = detector.detect(previous, current)

    assert transition == MediaHealthTransition(
        previous=previous,
        current=current,
        kind=HealthTransitionKind.DEGRADED,
    )


def test_degraded_to_healthy_is_recovered_transition() -> None:
    detector = MediaHealthTransitionDetector()

    previous = _health(HealthStatus.DEGRADED)
    current = _health(HealthStatus.HEALTHY)

    transition = detector.detect(previous, current)

    assert transition == MediaHealthTransition(
        previous=previous,
        current=current,
        kind=HealthTransitionKind.RECOVERED,
    )


@pytest.mark.parametrize(
    ("previous_status", "current_status"),
    [
        (HealthStatus.HEALTHY, HealthStatus.UNKNOWN),
        (HealthStatus.DEGRADED, HealthStatus.UNKNOWN),
        (HealthStatus.UNKNOWN, HealthStatus.HEALTHY),
        (HealthStatus.UNKNOWN, HealthStatus.DEGRADED),
    ],
)
def test_transition_to_or_from_unknown_is_unknown(
    previous_status: HealthStatus,
    current_status: HealthStatus,
) -> None:
    detector = MediaHealthTransitionDetector()

    previous = _health(previous_status)
    current = _health(current_status)

    transition = detector.detect(previous, current)

    assert transition == MediaHealthTransition(
        previous=previous,
        current=current,
        kind=HealthTransitionKind.UNKNOWN,
    )


@pytest.mark.parametrize(
    ("field_name", "current"),
    [
        (
            "profile_id",
            _health(
                HealthStatus.DEGRADED,
                profile_id="another-profile",
            ),
        ),
        (
            "service_id",
            _health(
                HealthStatus.DEGRADED,
                service_id="another-service",
            ),
        ),
        (
            "path_name",
            _health(
                HealthStatus.DEGRADED,
                path_name="another-path",
            ),
        ),
    ],
)
def test_different_media_identity_is_rejected(
    field_name: str,
    current: MediaHealth,
) -> None:
    detector = MediaHealthTransitionDetector()

    previous = _health(HealthStatus.HEALTHY)

    with pytest.raises(
        ValueError,
        match="identity",
    ):
        detector.detect(previous, current)


def test_none_path_is_valid_when_identity_matches() -> None:
    detector = MediaHealthTransitionDetector()

    previous = _health(
        HealthStatus.HEALTHY,
        path_name=None,
    )
    current = _health(
        HealthStatus.DEGRADED,
        path_name=None,
    )

    transition = detector.detect(previous, current)

    assert transition is not None
    assert transition.kind is HealthTransitionKind.DEGRADED


def test_transition_preserves_exact_media_health_objects() -> None:
    detector = MediaHealthTransitionDetector()

    previous = _health(HealthStatus.HEALTHY)
    current = _health(HealthStatus.DEGRADED)

    transition = detector.detect(previous, current)

    assert transition is not None
    assert transition.previous is previous
    assert transition.current is current


def test_previous_must_be_media_health_or_none() -> None:
    detector = MediaHealthTransitionDetector()

    with pytest.raises(TypeError):
        detector.detect(
            object(),  # type: ignore[arg-type]
            _health(HealthStatus.HEALTHY),
        )


def test_current_must_be_media_health() -> None:
    detector = MediaHealthTransitionDetector()

    with pytest.raises(TypeError):
        detector.detect(
            _health(HealthStatus.HEALTHY),
            object(),  # type: ignore[arg-type]
        )


def test_transition_requires_media_health_values() -> None:
    health = _health(HealthStatus.HEALTHY)

    with pytest.raises(TypeError):
        MediaHealthTransition(
            previous=object(),  # type: ignore[arg-type]
            current=health,
            kind=HealthTransitionKind.DEGRADED,
        )

    with pytest.raises(TypeError):
        MediaHealthTransition(
            previous=health,
            current=object(),  # type: ignore[arg-type]
            kind=HealthTransitionKind.DEGRADED,
        )


def test_transition_requires_health_transition_kind() -> None:
    previous = _health(HealthStatus.HEALTHY)
    current = _health(HealthStatus.DEGRADED)

    with pytest.raises(TypeError):
        MediaHealthTransition(
            previous=previous,
            current=current,
            kind="DEGRADED",  # type: ignore[arg-type]
        )
