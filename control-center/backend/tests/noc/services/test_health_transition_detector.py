import pytest

from app.noc.domain.node_health import (
    NodeHealth,
    NodeHealthState,
)
from app.noc.services.health_transition_detector import (
    HealthTransition,
    HealthTransitionDetector,
    HealthTransitionKind,
)


def health(state: NodeHealthState) -> NodeHealth:
    return NodeHealth(state)


def test_first_observation_has_no_transition():
    detector = HealthTransitionDetector()

    result = detector.detect(
        None,
        health(NodeHealthState.HEALTHY),
    )

    assert result is None


def test_same_state_has_no_transition():
    detector = HealthTransitionDetector()

    result = detector.detect(
        health(NodeHealthState.HEALTHY),
        health(NodeHealthState.HEALTHY),
    )

    assert result is None


def test_healthy_to_warning_is_degraded():
    detector = HealthTransitionDetector()

    result = detector.detect(
        health(NodeHealthState.HEALTHY),
        health(NodeHealthState.WARNING),
    )

    assert isinstance(result, HealthTransition)
    assert result.kind is HealthTransitionKind.DEGRADED
    assert result.previous.state is NodeHealthState.HEALTHY
    assert result.current.state is NodeHealthState.WARNING


def test_warning_to_degraded_is_degraded():
    detector = HealthTransitionDetector()

    result = detector.detect(
        health(NodeHealthState.WARNING),
        health(NodeHealthState.DEGRADED),
    )

    assert result is not None
    assert result.kind is HealthTransitionKind.DEGRADED


def test_degraded_to_critical_is_degraded():
    detector = HealthTransitionDetector()

    result = detector.detect(
        health(NodeHealthState.DEGRADED),
        health(NodeHealthState.CRITICAL),
    )

    assert result is not None
    assert result.kind is HealthTransitionKind.DEGRADED


def test_critical_to_degraded_is_improved():
    detector = HealthTransitionDetector()

    result = detector.detect(
        health(NodeHealthState.CRITICAL),
        health(NodeHealthState.DEGRADED),
    )

    assert result is not None
    assert result.kind is HealthTransitionKind.IMPROVED


def test_degraded_to_warning_is_improved():
    detector = HealthTransitionDetector()

    result = detector.detect(
        health(NodeHealthState.DEGRADED),
        health(NodeHealthState.WARNING),
    )

    assert result is not None
    assert result.kind is HealthTransitionKind.IMPROVED


def test_warning_to_healthy_is_recovered():
    detector = HealthTransitionDetector()

    result = detector.detect(
        health(NodeHealthState.WARNING),
        health(NodeHealthState.HEALTHY),
    )

    assert result is not None
    assert result.kind is HealthTransitionKind.RECOVERED


def test_critical_to_healthy_is_recovered():
    detector = HealthTransitionDetector()

    result = detector.detect(
        health(NodeHealthState.CRITICAL),
        health(NodeHealthState.HEALTHY),
    )

    assert result is not None
    assert result.kind is HealthTransitionKind.RECOVERED


def test_transition_to_unknown_is_unknown():
    detector = HealthTransitionDetector()

    result = detector.detect(
        health(NodeHealthState.HEALTHY),
        health(NodeHealthState.UNKNOWN),
    )

    assert result is not None
    assert result.kind is HealthTransitionKind.UNKNOWN


def test_transition_from_unknown_is_unknown():
    detector = HealthTransitionDetector()

    result = detector.detect(
        health(NodeHealthState.UNKNOWN),
        health(NodeHealthState.HEALTHY),
    )

    assert result is not None
    assert result.kind is HealthTransitionKind.UNKNOWN


def test_previous_requires_node_health_or_none():
    detector = HealthTransitionDetector()

    with pytest.raises(TypeError):
        detector.detect(
            object(),  # type: ignore[arg-type]
            health(NodeHealthState.HEALTHY),
        )


def test_current_requires_node_health():
    detector = HealthTransitionDetector()

    with pytest.raises(TypeError):
        detector.detect(
            health(NodeHealthState.HEALTHY),
            object(),  # type: ignore[arg-type]
        )
