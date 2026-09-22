"""Contract tests for MediaOperationalCycleRuntime."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from app.domain.streaming.health import HealthStatus
from app.domain.streaming.media_health import MediaHealth
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
    22,
    19,
    30,
    tzinfo=timezone.utc,
)


def make_operational_runtime(
    *,
    event_service=None,
) -> MediaOperationalRuntime:
    if event_service is None:
        event_service = Mock()

    return MediaOperationalRuntime(
        transition_detector=(
            MediaHealthTransitionDetector()
        ),
        transition_event_service=event_service,
    )


def make_node_id() -> NodeId:
    return NodeId.create(
        id="streaming-core",
        name="streaming",
        display_name="Streaming Core",
    )


def make_health(
    profile_id: str,
    service_id: str,
    path_name: str | None,
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
    *,
    profile_id: str,
    service_id: str,
    path_name: str,
    health: MediaHealth,
):
    result = Mock(
        spec=MediaObservationRuntimeProfileResult
    )
    result.stabilized_health = health
    return result


def test_process_cycle_forwards_each_stabilized_health_in_order():
    operational_runtime = make_operational_runtime()
    operational_runtime.process_health = Mock()

    cycle_runtime = MediaOperationalCycleRuntime(
        operational_runtime=operational_runtime
    )

    node_id = make_node_id()
    instance_id = NodeInstanceId(
        "streaming-primary"
    )

    health_a = make_health(
        "profile-a",
        "service-a",
        "feed-a",
    )
    health_b = make_health(
        "profile-b",
        "service-b",
        "feed-b",
        HealthStatus.DEGRADED,
    )

    profile_a = make_profile_result(
        profile_id="profile-a",
        service_id="service-a",
        path_name="feed-a",
        health=health_a,
    )
    profile_b = make_profile_result(
        profile_id="profile-b",
        service_id="service-b",
        path_name="feed-b",
        health=health_b,
    )

    cycle = MediaObservationRuntimeResult(
        observed_at=NOW,
        profiles=(
            profile_a,
            profile_b,
        ),
    )

    cycle_runtime.process_cycle(
        node_id=node_id,
        instance_id=instance_id,
        observation_result=cycle,
    )

    assert (
        operational_runtime.process_health.call_count
        == 2
    )

    first_call = (
        operational_runtime.process_health.call_args_list[0]
    )
    second_call = (
        operational_runtime.process_health.call_args_list[1]
    )

    assert first_call.kwargs == {
        "node_id": node_id,
        "instance_id": instance_id,
        "health": health_a,
        "observed_at": NOW,
    }

    assert second_call.kwargs == {
        "node_id": node_id,
        "instance_id": instance_id,
        "health": health_b,
        "observed_at": NOW,
    }


def test_process_cycle_with_no_profiles_does_nothing():
    operational_runtime = make_operational_runtime()
    operational_runtime.process_health = Mock()

    cycle_runtime = MediaOperationalCycleRuntime(
        operational_runtime=operational_runtime
    )

    cycle_runtime.process_cycle(
        node_id=make_node_id(),
        instance_id=NodeInstanceId(
            "streaming-primary"
        ),
        observation_result=(
            MediaObservationRuntimeResult(
                observed_at=NOW,
                profiles=(),
            )
        ),
    )

    operational_runtime.process_health.assert_not_called()


def test_process_cycle_is_fail_fast_per_profile():
    operational_runtime = make_operational_runtime()

    operational_runtime.process_health = Mock(
        side_effect=(
            None,
            RuntimeError("synthetic profile failure"),
            None,
        )
    )

    cycle_runtime = MediaOperationalCycleRuntime(
        operational_runtime=operational_runtime
    )

    node_id = make_node_id()
    instance_id = NodeInstanceId(
        "streaming-primary"
    )

    health_a = make_health(
        "profile-a",
        "service-a",
        "feed-a",
    )
    health_b = make_health(
        "profile-b",
        "service-b",
        "feed-b",
        HealthStatus.DEGRADED,
    )
    health_c = make_health(
        "profile-c",
        "service-c",
        "feed-c",
    )

    cycle = MediaObservationRuntimeResult(
        observed_at=NOW,
        profiles=(
            make_profile_result(
                profile_id="profile-a",
                service_id="service-a",
                path_name="feed-a",
                health=health_a,
            ),
            make_profile_result(
                profile_id="profile-b",
                service_id="service-b",
                path_name="feed-b",
                health=health_b,
            ),
            make_profile_result(
                profile_id="profile-c",
                service_id="service-c",
                path_name="feed-c",
                health=health_c,
            ),
        ),
    )

    with pytest.raises(
        RuntimeError,
        match="synthetic profile failure",
    ):
        cycle_runtime.process_cycle(
            node_id=node_id,
            instance_id=instance_id,
            observation_result=cycle,
        )

    assert (
        operational_runtime.process_health.call_count
        == 2
    )


def test_process_cycle_validates_arguments():
    operational_runtime = make_operational_runtime()

    cycle_runtime = MediaOperationalCycleRuntime(
        operational_runtime=operational_runtime
    )

    node_id = make_node_id()
    instance_id = NodeInstanceId(
        "streaming-primary"
    )
    cycle = MediaObservationRuntimeResult(
        observed_at=NOW,
        profiles=(),
    )

    with pytest.raises(
        TypeError,
        match="node_id",
    ):
        cycle_runtime.process_cycle(
            node_id="bad",
            instance_id=instance_id,
            observation_result=cycle,
        )

    with pytest.raises(
        TypeError,
        match="instance_id",
    ):
        cycle_runtime.process_cycle(
            node_id=node_id,
            instance_id="bad",
            observation_result=cycle,
        )

    with pytest.raises(
        TypeError,
        match="observation_result",
    ):
        cycle_runtime.process_cycle(
            node_id=node_id,
            instance_id=instance_id,
            observation_result="bad",
        )


def test_constructor_requires_operational_runtime():
    with pytest.raises(
        TypeError,
        match="operational_runtime",
    ):
        MediaOperationalCycleRuntime(
            operational_runtime=None
        )
