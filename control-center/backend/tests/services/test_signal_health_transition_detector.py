"""Contract tests for Signal Health transition detection.

ENG-013C — Signal Health Events

These tests define transition semantics only.

The detector must not:
- create or persist NOC events;
- evaluate Media Health;
- evaluate Source Transport Health;
- reinterpret Signal Health;
- own runtime state beyond comparing the supplied conclusions.
"""

from __future__ import annotations

import pytest

from app.domain.streaming.health import HealthStatus
from app.domain.streaming.signal_health import SignalHealth
from app.noc.services.health_transition_detector import (
    HealthTransitionKind,
)
from app.services.signal_health_transition_detector import (
    SignalHealthTransition,
    SignalHealthTransitionDetector,
)


PROFILE_ID = "impact-main"
SERVICE_ID = "impact"
PATH_NAME = "impact"


def _health(
    *,
    status: HealthStatus,
    media_status: HealthStatus | None = None,
    transport_status: HealthStatus | None = None,
    profile_id: str = PROFILE_ID,
    service_id: str = SERVICE_ID,
    path_name: str | None = PATH_NAME,
) -> SignalHealth:
    """Build one already-evaluated Signal Health conclusion."""

    effective_media_status = (
        status
        if media_status is None
        else media_status
    )

    effective_transport_status = (
        status
        if transport_status is None
        else transport_status
    )

    return SignalHealth(
        profile_id=profile_id,
        service_id=service_id,
        path_name=path_name,
        media_status=effective_media_status,
        transport_status=effective_transport_status,
        status=status,
    )


@pytest.mark.parametrize(
    ("previous_status", "current_status", "expected_kind"),
    [
        (
            HealthStatus.HEALTHY,
            HealthStatus.DEGRADED,
            HealthTransitionKind.DEGRADED,
        ),
        (
            HealthStatus.DEGRADED,
            HealthStatus.CRITICAL,
            HealthTransitionKind.DEGRADED,
        ),
        (
            HealthStatus.HEALTHY,
            HealthStatus.CRITICAL,
            HealthTransitionKind.DEGRADED,
        ),
        (
            HealthStatus.CRITICAL,
            HealthStatus.DEGRADED,
            HealthTransitionKind.IMPROVED,
        ),
        (
            HealthStatus.DEGRADED,
            HealthStatus.HEALTHY,
            HealthTransitionKind.RECOVERED,
        ),
        (
            HealthStatus.CRITICAL,
            HealthStatus.HEALTHY,
            HealthTransitionKind.RECOVERED,
        ),
        (
            HealthStatus.HEALTHY,
            HealthStatus.UNKNOWN,
            HealthTransitionKind.UNKNOWN,
        ),
        (
            HealthStatus.DEGRADED,
            HealthStatus.UNKNOWN,
            HealthTransitionKind.UNKNOWN,
        ),
        (
            HealthStatus.CRITICAL,
            HealthStatus.UNKNOWN,
            HealthTransitionKind.UNKNOWN,
        ),
        (
            HealthStatus.UNKNOWN,
            HealthStatus.HEALTHY,
            HealthTransitionKind.UNKNOWN,
        ),
        (
            HealthStatus.UNKNOWN,
            HealthStatus.DEGRADED,
            HealthTransitionKind.UNKNOWN,
        ),
        (
            HealthStatus.UNKNOWN,
            HealthStatus.CRITICAL,
            HealthTransitionKind.UNKNOWN,
        ),
    ],
)
def test_status_change_is_classified(
    previous_status: HealthStatus,
    current_status: HealthStatus,
    expected_kind: HealthTransitionKind,
) -> None:
    detector = SignalHealthTransitionDetector()

    previous = _health(status=previous_status)
    current = _health(status=current_status)

    transition = detector.detect(previous, current)

    assert transition == SignalHealthTransition(
        previous=previous,
        current=current,
        kind=expected_kind,
    )

    assert transition.previous is previous
    assert transition.current is current
    assert transition.kind is expected_kind


def test_first_observation_does_not_create_transition() -> None:
    detector = SignalHealthTransitionDetector()

    transition = detector.detect(
        None,
        _health(status=HealthStatus.HEALTHY),
    )

    assert transition is None


def test_unchanged_aggregate_status_does_not_create_transition() -> None:
    detector = SignalHealthTransitionDetector()

    previous = _health(
        status=HealthStatus.DEGRADED,
        media_status=HealthStatus.HEALTHY,
        transport_status=HealthStatus.DEGRADED,
    )

    current = _health(
        status=HealthStatus.DEGRADED,
        media_status=HealthStatus.DEGRADED,
        transport_status=HealthStatus.HEALTHY,
    )

    transition = detector.detect(previous, current)

    assert transition is None


def test_transition_preserves_component_statuses_exactly() -> None:
    detector = SignalHealthTransitionDetector()

    previous = _health(
        status=HealthStatus.HEALTHY,
        media_status=HealthStatus.HEALTHY,
        transport_status=HealthStatus.HEALTHY,
    )

    current = _health(
        status=HealthStatus.DEGRADED,
        media_status=HealthStatus.HEALTHY,
        transport_status=HealthStatus.DEGRADED,
    )

    transition = detector.detect(previous, current)

    assert transition is not None

    assert transition.previous is previous
    assert transition.current is current

    assert (
        transition.previous.media_status
        is HealthStatus.HEALTHY
    )
    assert (
        transition.previous.transport_status
        is HealthStatus.HEALTHY
    )
    assert (
        transition.current.media_status
        is HealthStatus.HEALTHY
    )
    assert (
        transition.current.transport_status
        is HealthStatus.DEGRADED
    )


@pytest.mark.parametrize(
    ("identity_field", "replacement"),
    [
        ("profile_id", "another-profile"),
        ("service_id", "another-service"),
        ("path_name", "another-path"),
    ],
)
def test_identity_change_is_rejected(
    identity_field: str,
    replacement: str,
) -> None:
    detector = SignalHealthTransitionDetector()

    previous = _health(status=HealthStatus.HEALTHY)

    current_kwargs = {
        "status": HealthStatus.DEGRADED,
        "profile_id": PROFILE_ID,
        "service_id": SERVICE_ID,
        "path_name": PATH_NAME,
    }
    current_kwargs[identity_field] = replacement

    current = _health(**current_kwargs)

    with pytest.raises(ValueError):
        detector.detect(previous, current)


def test_none_path_is_valid_when_identity_matches() -> None:
    detector = SignalHealthTransitionDetector()

    previous = _health(
        status=HealthStatus.HEALTHY,
        path_name=None,
    )

    current = _health(
        status=HealthStatus.DEGRADED,
        path_name=None,
    )

    transition = detector.detect(previous, current)

    assert transition == SignalHealthTransition(
        previous=previous,
        current=current,
        kind=HealthTransitionKind.DEGRADED,
    )


def test_invalid_previous_type_is_rejected() -> None:
    detector = SignalHealthTransitionDetector()

    with pytest.raises(TypeError):
        detector.detect(
            "not-signal-health",  # type: ignore[arg-type]
            _health(status=HealthStatus.HEALTHY),
        )


def test_invalid_current_type_is_rejected() -> None:
    detector = SignalHealthTransitionDetector()

    with pytest.raises(TypeError):
        detector.detect(
            None,
            "not-signal-health",  # type: ignore[arg-type]
        )


def test_transition_rejects_invalid_previous_type() -> None:
    current = _health(status=HealthStatus.DEGRADED)

    with pytest.raises(TypeError):
        SignalHealthTransition(
            previous="not-signal-health",  # type: ignore[arg-type]
            current=current,
            kind=HealthTransitionKind.DEGRADED,
        )


def test_transition_rejects_invalid_current_type() -> None:
    previous = _health(status=HealthStatus.HEALTHY)

    with pytest.raises(TypeError):
        SignalHealthTransition(
            previous=previous,
            current="not-signal-health",  # type: ignore[arg-type]
            kind=HealthTransitionKind.DEGRADED,
        )


def test_transition_rejects_invalid_kind_type() -> None:
    previous = _health(status=HealthStatus.HEALTHY)
    current = _health(status=HealthStatus.DEGRADED)

    with pytest.raises(TypeError):
        SignalHealthTransition(
            previous=previous,
            current=current,
            kind="degraded",  # type: ignore[arg-type]
        )
