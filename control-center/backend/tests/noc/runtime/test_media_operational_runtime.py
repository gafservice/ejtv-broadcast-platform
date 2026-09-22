from datetime import datetime, timezone

import pytest

from app.domain.streaming.health import HealthStatus
from app.domain.streaming.media_health import MediaHealth
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.runtime.media_operational_runtime import (
    MediaOperationalRuntime,
)
from app.services.media_health_transition_detector import (
    MediaHealthTransitionDetector,
)


NOW = datetime(
    2026,
    9,
    22,
    23,
    0,
    tzinfo=timezone.utc,
)


class RecordingEventService:
    def __init__(self) -> None:
        self.calls = []

    def process_transition(
        self,
        *,
        node_id,
        instance_id,
        transition,
        timestamp,
    ):
        self.calls.append(
            {
                "node_id": node_id,
                "instance_id": instance_id,
                "transition": transition,
                "timestamp": timestamp,
            }
        )
        return transition


def make_health(
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


def make_runtime():
    event_service = RecordingEventService()

    runtime = MediaOperationalRuntime(
        transition_detector=(
            MediaHealthTransitionDetector()
        ),
        transition_event_service=event_service,
    )

    return runtime, event_service


def test_first_observation_establishes_baseline_without_event():
    runtime, event_service = make_runtime()

    result = runtime.process_health(
        node_id=NodeId.create(
            id="streaming-core",
            name="streaming",
            display_name="Streaming Core",
        ),
        instance_id=NodeInstanceId(
            "streaming-primary"
        ),
        health=make_health(
            HealthStatus.HEALTHY
        ),
        observed_at=NOW,
    )

    assert result.transition is None
    assert result.event_result is None
    assert event_service.calls == []


def test_same_stabilized_status_does_not_emit_duplicate_event():
    runtime, event_service = make_runtime()

    node_id = NodeId.create(
            id="streaming-core",
            name="streaming",
            display_name="Streaming Core",
        )
    instance_id = NodeInstanceId(
        "streaming-primary"
    )

    runtime.process_health(
        node_id=node_id,
        instance_id=instance_id,
        health=make_health(
            HealthStatus.HEALTHY
        ),
        observed_at=NOW,
    )

    result = runtime.process_health(
        node_id=node_id,
        instance_id=instance_id,
        health=make_health(
            HealthStatus.HEALTHY
        ),
        observed_at=NOW,
    )

    assert result.transition is None
    assert result.event_result is None
    assert event_service.calls == []


def test_health_change_emits_exactly_one_transition_event():
    runtime, event_service = make_runtime()

    node_id = NodeId.create(
            id="streaming-core",
            name="streaming",
            display_name="Streaming Core",
        )
    instance_id = NodeInstanceId(
        "streaming-primary"
    )

    healthy = make_health(
        HealthStatus.HEALTHY
    )
    degraded = make_health(
        HealthStatus.DEGRADED
    )

    runtime.process_health(
        node_id=node_id,
        instance_id=instance_id,
        health=healthy,
        observed_at=NOW,
    )

    result = runtime.process_health(
        node_id=node_id,
        instance_id=instance_id,
        health=degraded,
        observed_at=NOW,
    )

    assert result.transition is not None
    assert (
        result.transition.previous.status
        is HealthStatus.HEALTHY
    )
    assert (
        result.transition.current.status
        is HealthStatus.DEGRADED
    )

    assert len(event_service.calls) == 1

    call = event_service.calls[0]

    assert call["node_id"] == node_id
    assert call["instance_id"] == instance_id
    assert (
        call["transition"]
        is result.transition
    )
    assert call["timestamp"] == NOW


def test_repeated_degraded_does_not_emit_duplicate_event():
    runtime, event_service = make_runtime()

    node_id = NodeId.create(
            id="streaming-core",
            name="streaming",
            display_name="Streaming Core",
        )
    instance_id = NodeInstanceId(
        "streaming-primary"
    )

    runtime.process_health(
        node_id=node_id,
        instance_id=instance_id,
        health=make_health(
            HealthStatus.HEALTHY
        ),
        observed_at=NOW,
    )

    runtime.process_health(
        node_id=node_id,
        instance_id=instance_id,
        health=make_health(
            HealthStatus.DEGRADED
        ),
        observed_at=NOW,
    )

    result = runtime.process_health(
        node_id=node_id,
        instance_id=instance_id,
        health=make_health(
            HealthStatus.DEGRADED
        ),
        observed_at=NOW,
    )

    assert result.transition is None
    assert result.event_result is None
    assert len(event_service.calls) == 1


def test_recovery_emits_one_recovered_transition():
    runtime, event_service = make_runtime()

    node_id = NodeId.create(
            id="streaming-core",
            name="streaming",
            display_name="Streaming Core",
        )
    instance_id = NodeInstanceId(
        "streaming-primary"
    )

    runtime.process_health(
        node_id=node_id,
        instance_id=instance_id,
        health=make_health(
            HealthStatus.HEALTHY
        ),
        observed_at=NOW,
    )

    runtime.process_health(
        node_id=node_id,
        instance_id=instance_id,
        health=make_health(
            HealthStatus.DEGRADED
        ),
        observed_at=NOW,
    )

    result = runtime.process_health(
        node_id=node_id,
        instance_id=instance_id,
        health=make_health(
            HealthStatus.HEALTHY
        ),
        observed_at=NOW,
    )

    assert result.transition is not None
    assert (
        result.transition.current.status
        is HealthStatus.HEALTHY
    )

    assert len(event_service.calls) == 2


def test_profiles_keep_independent_previous_health():
    runtime, event_service = make_runtime()

    node_id = NodeId.create(
            id="streaming-core",
            name="streaming",
            display_name="Streaming Core",
        )
    instance_id = NodeInstanceId(
        "streaming-primary"
    )

    runtime.process_health(
        node_id=node_id,
        instance_id=instance_id,
        health=make_health(
            HealthStatus.HEALTHY,
            profile_id="profile-a",
            service_id="service-a",
            path_name="path-a",
        ),
        observed_at=NOW,
    )

    runtime.process_health(
        node_id=node_id,
        instance_id=instance_id,
        health=make_health(
            HealthStatus.HEALTHY,
            profile_id="profile-b",
            service_id="service-b",
            path_name="path-b",
        ),
        observed_at=NOW,
    )

    runtime.process_health(
        node_id=node_id,
        instance_id=instance_id,
        health=make_health(
            HealthStatus.DEGRADED,
            profile_id="profile-a",
            service_id="service-a",
            path_name="path-a",
        ),
        observed_at=NOW,
    )

    assert len(event_service.calls) == 1

    transition = (
        event_service.calls[0][
            "transition"
        ]
    )

    assert (
        transition.current.profile_id
        == "profile-a"
    )


def test_path_none_is_valid_identity():
    runtime, event_service = make_runtime()

    node_id = NodeId.create(
            id="streaming-core",
            name="streaming",
            display_name="Streaming Core",
        )
    instance_id = NodeInstanceId(
        "streaming-primary"
    )

    runtime.process_health(
        node_id=node_id,
        instance_id=instance_id,
        health=make_health(
            HealthStatus.HEALTHY,
            path_name=None,
        ),
        observed_at=NOW,
    )

    result = runtime.process_health(
        node_id=node_id,
        instance_id=instance_id,
        health=make_health(
            HealthStatus.DEGRADED,
            path_name=None,
        ),
        observed_at=NOW,
    )

    assert result.transition is not None
    assert len(event_service.calls) == 1


@pytest.mark.parametrize(
    ("argument", "value", "message"),
    [
        (
            "node_id",
            "streaming-core",
            "node_id must be a NodeId",
        ),
        (
            "instance_id",
            "streaming-primary",
            "instance_id must be a NodeInstanceId",
        ),
        (
            "health",
            object(),
            "health must be a MediaHealth",
        ),
        (
            "observed_at",
            "2026-09-22T23:00:00Z",
            "observed_at must be a datetime",
        ),
    ],
)
def test_process_health_rejects_invalid_arguments(
    argument,
    value,
    message,
):
    runtime, _ = make_runtime()

    kwargs = {
        "node_id": NodeId.create(
            id="streaming-core",
            name="streaming",
            display_name="Streaming Core",
        ),
        "instance_id": NodeInstanceId(
            "streaming-primary"
        ),
        "health": make_health(
            HealthStatus.HEALTHY
        ),
        "observed_at": NOW,
    }

    kwargs[argument] = value

    with pytest.raises(
        TypeError,
        match=message,
    ):
        runtime.process_health(**kwargs)


def test_failed_event_persistence_does_not_consume_transition():
    class FailOnceEventService:
        def __init__(self) -> None:
            self.calls = []
            self._failed = False

        def process_transition(
            self,
            *,
            node_id,
            instance_id,
            transition,
            timestamp,
        ):
            self.calls.append(
                transition
            )

            if not self._failed:
                self._failed = True
                raise RuntimeError(
                    "synthetic event persistence failure"
                )

            return transition

    event_service = FailOnceEventService()

    runtime = MediaOperationalRuntime(
        transition_detector=(
            MediaHealthTransitionDetector()
        ),
        transition_event_service=event_service,
    )

    node_id = NodeId.create(
        id="streaming-core",
        name="streaming",
        display_name="Streaming Core",
    )

    instance_id = NodeInstanceId(
        "streaming-primary"
    )

    runtime.process_health(
        node_id=node_id,
        instance_id=instance_id,
        health=make_health(
            HealthStatus.HEALTHY
        ),
        observed_at=NOW,
    )

    with pytest.raises(
        RuntimeError,
        match="synthetic event persistence failure",
    ):
        runtime.process_health(
            node_id=node_id,
            instance_id=instance_id,
            health=make_health(
                HealthStatus.DEGRADED
            ),
            observed_at=NOW,
        )

    retry = runtime.process_health(
        node_id=node_id,
        instance_id=instance_id,
        health=make_health(
            HealthStatus.DEGRADED
        ),
        observed_at=NOW,
    )

    assert retry.transition is not None

    assert (
        retry.transition.previous.status
        is HealthStatus.HEALTHY
    )

    assert (
        retry.transition.current.status
        is HealthStatus.DEGRADED
    )

    assert len(event_service.calls) == 2
