"""Contract tests for Media Health current-state publication.

The current-state projection belongs to the operational cycle boundary,
not to MediaObservationRuntime.

For each profile, the stabilized MediaHealth value is published before
the downstream operational processing for that same profile.

The cycle remains fail-fast.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from app.domain.streaming.health import HealthStatus
from app.domain.streaming.media_health import MediaHealth
from app.noc.current_state.media_health_current_state import (
    MediaHealthCurrentStateRepository,
)
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.runtime.media_observation_runtime import (
    MediaObservationRuntimeProfileResult,
    MediaObservationRuntimeResult,
)
from app.noc.runtime.media_operational_cycle_runtime import (
    MediaOperationalCycleRuntime,
)
from app.noc.runtime.media_operational_runtime import (
    MediaOperationalRuntime,
)
from app.services.media_health_transition_detector import (
    MediaHealthTransitionDetector,
)


NOW = datetime(
    2026,
    9,
    24,
    12,
    0,
    tzinfo=timezone.utc,
)


def make_node_id() -> NodeId:
    return NodeId.create(
        id="streaming-core",
        name="streaming",
        display_name="Streaming Core",
    )


def make_health(
    *,
    profile_id: str = "impact-main",
    service_id: str = "impact",
    path_name: str = "impact",
    status: HealthStatus = HealthStatus.HEALTHY,
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


def make_profile_result(
    health: MediaHealth,
) -> MediaObservationRuntimeProfileResult:
    result = Mock(
        spec=MediaObservationRuntimeProfileResult
    )
    result.stabilized_health = health
    return result


def make_cycle(
    *health_values: MediaHealth,
) -> MediaObservationRuntimeResult:
    return MediaObservationRuntimeResult(
        observed_at=NOW,
        profiles=tuple(
            make_profile_result(health)
            for health in health_values
        ),
    )


def make_operational_runtime() -> MediaOperationalRuntime:
    runtime = MediaOperationalRuntime(
        transition_detector=(
            MediaHealthTransitionDetector()
        ),
        transition_event_service=Mock(),
    )
    runtime.process_health = Mock()
    return runtime


def test_process_cycle_publishes_current_state_before_operational_health():
    health = make_health()

    calls: list[str] = []

    repository = Mock(
        spec=MediaHealthCurrentStateRepository
    )
    repository.save.side_effect = (
        lambda **_: calls.append("current-state")
    )

    operational_runtime = make_operational_runtime()
    operational_runtime.process_health.side_effect = (
        lambda **_: calls.append("operational-health")
    )

    runtime = MediaOperationalCycleRuntime(
        operational_runtime=operational_runtime,
        current_state_repository=repository,
    )

    runtime.process_cycle(
        node_id=make_node_id(),
        instance_id=NodeInstanceId(
            "streaming-primary"
        ),
        observation_result=make_cycle(health),
    )

    assert calls == [
        "current-state",
        "operational-health",
    ]


def test_process_cycle_publishes_stabilized_health_identity_and_time():
    health = make_health(
        profile_id="impact-main",
        service_id="impact",
        path_name="impact",
        status=HealthStatus.DEGRADED,
    )

    repository = Mock(
        spec=MediaHealthCurrentStateRepository
    )
    operational_runtime = make_operational_runtime()

    runtime = MediaOperationalCycleRuntime(
        operational_runtime=operational_runtime,
        current_state_repository=repository,
    )

    runtime.process_cycle(
        node_id=make_node_id(),
        instance_id=NodeInstanceId(
            "streaming-primary"
        ),
        observation_result=make_cycle(health),
    )

    repository.save.assert_called_once()

    state = repository.save.call_args.kwargs["state"]

    assert state.profile_id == "impact-main"
    assert state.service_id == "impact"
    assert state.path_name == "impact"
    assert state.observed_at == NOW
    assert state.health is health


def test_repository_failure_prevents_operational_processing_for_profile():
    health = make_health()

    repository = Mock(
        spec=MediaHealthCurrentStateRepository
    )
    repository.save.side_effect = RuntimeError(
        "synthetic current-state failure"
    )

    operational_runtime = make_operational_runtime()

    runtime = MediaOperationalCycleRuntime(
        operational_runtime=operational_runtime,
        current_state_repository=repository,
    )

    with pytest.raises(
        RuntimeError,
        match="synthetic current-state failure",
    ):
        runtime.process_cycle(
            node_id=make_node_id(),
            instance_id=NodeInstanceId(
                "streaming-primary"
            ),
            observation_result=make_cycle(health),
        )

    operational_runtime.process_health.assert_not_called()


def test_current_state_and_operational_processing_preserve_profile_order():
    health_a = make_health(
        profile_id="profile-a",
        service_id="service-a",
        path_name="feed-a",
    )
    health_b = make_health(
        profile_id="profile-b",
        service_id="service-b",
        path_name="feed-b",
        status=HealthStatus.DEGRADED,
    )

    calls: list[tuple[str, str]] = []

    repository = Mock(
        spec=MediaHealthCurrentStateRepository
    )

    def save(*, state):
        calls.append(
            ("current-state", state.profile_id)
        )

    repository.save.side_effect = save

    operational_runtime = make_operational_runtime()

    def process_health(*, health, **_):
        calls.append(
            ("operational-health", health.profile_id)
        )

    operational_runtime.process_health.side_effect = (
        process_health
    )

    runtime = MediaOperationalCycleRuntime(
        operational_runtime=operational_runtime,
        current_state_repository=repository,
    )

    runtime.process_cycle(
        node_id=make_node_id(),
        instance_id=NodeInstanceId(
            "streaming-primary"
        ),
        observation_result=make_cycle(
            health_a,
            health_b,
        ),
    )

    assert calls == [
        ("current-state", "profile-a"),
        ("operational-health", "profile-a"),
        ("current-state", "profile-b"),
        ("operational-health", "profile-b"),
    ]
