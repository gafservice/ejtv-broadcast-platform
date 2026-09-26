import pytest
from datetime import datetime, timezone
from unittest.mock import Mock

from app.domain.streaming.expected_media_profile import (
    ExpectedMediaProfile,
    ExpectedVideoProfile,
    MediaPresenceExpectation,
)
from app.domain.streaming.health import HealthStatus
from app.domain.streaming.media_observation import (
    EvidenceAvailability,
    InputMediaObservation,
    VideoTrackObservation,
)
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.runtime.media_observation_runtime import (
    MediaObservationRuntime,
    MediaObservationRuntimeResult,
)
from app.noc.services.media_observation_source_resolver import (
    MediaObservationSourceResolver,
)
from app.services.media_health_stabilizer import (
    MediaHealthStabilizer,
)


def test_run_once_composes_one_resolvable_media_profile() -> None:
    observed_at = datetime(
        2026,
        9,
        22,
        18,
        0,
        tzinfo=timezone.utc,
    )

    node_id = NodeId(
        id="node-a",
        name="node-a",
        display_name="Node A",
        created_at=observed_at,
    )
    instance_id = NodeInstanceId("instance-a")

    profile = ExpectedMediaProfile(
        profile_id="profile-a",
        service_id="service-a",
        path_name="feed-a",
        video=ExpectedVideoProfile(
            presence=MediaPresenceExpectation.REQUIRED,
            codec="h264",
        ),
    )

    observed_sources: list[str] = []

    class StubObserver:
        def observe(
            self,
            *,
            node_id,
            instance_id,
            service_id,
            source,
            observed_at,
            path_name=None,
        ):
            observed_sources.append(source)

            return InputMediaObservation(
                node_id=node_id,
                instance_id=instance_id,
                service_id=service_id,
                path_name=path_name,
                observed_at=observed_at,
                container=None,
                video=VideoTrackObservation(
                    availability=EvidenceAvailability.AVAILABLE,
                    codec="h264",
                ),
                audio=None,
            )

    runtime = MediaObservationRuntime(
        profiles=(profile,),
        source_resolver=MediaObservationSourceResolver(
            rtsp_base_url="rtsp://media-node.internal:8554",
        ),
        observer=StubObserver(),
        stabilizer=MediaHealthStabilizer(
            degradation_seconds=10.0,
            recovery_seconds=5.0,
        ),
        operational_cycle_runtime=_InertOperationalCycleRuntime(),
    )

    result = runtime.run_once(
        node_id=node_id,
        instance_id=instance_id,
        observed_at=observed_at,
    )

    assert result.observed_at == observed_at
    assert len(result.profiles) == 1

    profile_result = result.profiles[0]

    assert profile_result.profile is profile
    assert (
        profile_result.source
        == "rtsp://media-node.internal:8554/feed-a"
    )

    assert observed_sources == [
        "rtsp://media-node.internal:8554/feed-a"
    ]

    assert (
        profile_result.observation.node_id
        == node_id
    )
    assert (
        profile_result.observation.instance_id
        == instance_id
    )
    assert (
        profile_result.observation.service_id
        == "service-a"
    )
    assert (
        profile_result.observation.path_name
        == "feed-a"
    )
    assert (
        profile_result.observation.observed_at
        == observed_at
    )

    assert (
        profile_result.evaluation.profile_id
        == "profile-a"
    )
    assert (
        profile_result.evaluation.service_id
        == "service-a"
    )
    assert (
        profile_result.evaluation.path_name
        == "feed-a"
    )

    assert (
        profile_result.instantaneous_health.status
        is HealthStatus.HEALTHY
    )

    assert (
        profile_result.stabilized_health.status
        is HealthStatus.HEALTHY
    )


def test_run_once_with_no_profiles_returns_empty_cycle() -> None:
    observed_at = datetime(
        2026,
        9,
        22,
        18,
        5,
        tzinfo=timezone.utc,
    )

    node_id = NodeId(
        id="node-a",
        name="node-a",
        display_name="Node A",
        created_at=observed_at,
    )

    class ObserverMustNotRun:
        def observe(self, **kwargs):
            raise AssertionError(
                "observer must not run when there are no profiles"
            )

    runtime = MediaObservationRuntime(
        profiles=(),
        source_resolver=MediaObservationSourceResolver(
            rtsp_base_url="rtsp://media-node.internal:8554",
        ),
        observer=ObserverMustNotRun(),
        stabilizer=MediaHealthStabilizer(
            degradation_seconds=10.0,
            recovery_seconds=5.0,
        ),
        operational_cycle_runtime=_InertOperationalCycleRuntime(),
    )

    result = runtime.run_once(
        node_id=node_id,
        instance_id=NodeInstanceId("instance-a"),
        observed_at=observed_at,
    )

    assert result.observed_at == observed_at
    assert result.profiles == ()


def test_run_once_processes_multiple_profiles_in_order() -> None:
    observed_at = datetime(
        2026,
        9,
        22,
        18,
        10,
        tzinfo=timezone.utc,
    )

    node_id = NodeId(
        id="node-a",
        name="node-a",
        display_name="Node A",
        created_at=observed_at,
    )

    profiles = (
        ExpectedMediaProfile(
            profile_id="profile-a",
            service_id="service-a",
            path_name="feed-a",
            video=ExpectedVideoProfile(
                presence=MediaPresenceExpectation.REQUIRED,
                codec="h264",
            ),
        ),
        ExpectedMediaProfile(
            profile_id="profile-b",
            service_id="service-b",
            path_name="feed-b",
            video=ExpectedVideoProfile(
                presence=MediaPresenceExpectation.REQUIRED,
                codec="h264",
            ),
        ),
    )

    observed_calls: list[
        tuple[str, str | None, str]
    ] = []

    class StubObserver:
        def observe(
            self,
            *,
            node_id,
            instance_id,
            service_id,
            source,
            observed_at,
            path_name=None,
        ):
            observed_calls.append(
                (
                    service_id,
                    path_name,
                    source,
                )
            )

            return InputMediaObservation(
                node_id=node_id,
                instance_id=instance_id,
                service_id=service_id,
                path_name=path_name,
                observed_at=observed_at,
                container=None,
                video=VideoTrackObservation(
                    availability=EvidenceAvailability.AVAILABLE,
                    codec="h264",
                ),
                audio=None,
            )

    runtime = MediaObservationRuntime(
        profiles=profiles,
        source_resolver=MediaObservationSourceResolver(
            rtsp_base_url="rtsp://media-node.internal:8554",
        ),
        observer=StubObserver(),
        stabilizer=MediaHealthStabilizer(
            degradation_seconds=10.0,
            recovery_seconds=5.0,
        ),
        operational_cycle_runtime=_InertOperationalCycleRuntime(),
    )

    result = runtime.run_once(
        node_id=node_id,
        instance_id=NodeInstanceId("instance-a"),
        observed_at=observed_at,
    )

    assert [
        item.profile.profile_id
        for item in result.profiles
    ] == [
        "profile-a",
        "profile-b",
    ]

    assert observed_calls == [
        (
            "service-a",
            "feed-a",
            "rtsp://media-node.internal:8554/feed-a",
        ),
        (
            "service-b",
            "feed-b",
            "rtsp://media-node.internal:8554/feed-b",
        ),
    ]

    assert all(
        item.instantaneous_health.status
        is HealthStatus.HEALTHY
        for item in result.profiles
    )

    assert all(
        item.stabilized_health.status
        is HealthStatus.HEALTHY
        for item in result.profiles
    )


def test_run_once_skips_service_wide_profile_without_physical_path() -> None:
    observed_at = datetime(
        2026,
        9,
        22,
        18,
        15,
        tzinfo=timezone.utc,
    )

    node_id = NodeId(
        id="node-a",
        name="node-a",
        display_name="Node A",
        created_at=observed_at,
    )

    profile = ExpectedMediaProfile(
        profile_id="service-wide-profile",
        service_id="service-a",
        path_name=None,
        video=ExpectedVideoProfile(
            presence=MediaPresenceExpectation.REQUIRED,
            codec="h264",
        ),
    )

    class ObserverMustNotRun:
        def observe(self, **kwargs):
            raise AssertionError(
                "service-wide profile has no physical path"
            )

    runtime = MediaObservationRuntime(
        profiles=(profile,),
        source_resolver=MediaObservationSourceResolver(
            rtsp_base_url="rtsp://media-node.internal:8554",
        ),
        observer=ObserverMustNotRun(),
        stabilizer=MediaHealthStabilizer(
            degradation_seconds=10.0,
            recovery_seconds=5.0,
        ),
        operational_cycle_runtime=_InertOperationalCycleRuntime(),
    )

    result = runtime.run_once(
        node_id=node_id,
        instance_id=NodeInstanceId("instance-a"),
        observed_at=observed_at,
    )

    assert result.observed_at == observed_at
    assert result.profiles == ()


def test_run_once_receives_runtime_owner_identity_per_cycle() -> None:
    observed_at = datetime(
        2026,
        9,
        22,
        18,
        20,
        tzinfo=timezone.utc,
    )

    node_id = NodeId(
        id="node-owner",
        name="node-owner",
        display_name="Node Owner",
        created_at=observed_at,
    )
    instance_id = NodeInstanceId("instance-owner")

    profile = ExpectedMediaProfile(
        profile_id="profile-owner",
        service_id="service-owner",
        path_name="feed-owner",
        video=ExpectedVideoProfile(
            presence=MediaPresenceExpectation.REQUIRED,
            codec="h264",
        ),
    )

    observed_identity = []

    class StubObserver:
        def observe(
            self,
            *,
            node_id,
            instance_id,
            service_id,
            source,
            observed_at,
            path_name=None,
        ):
            observed_identity.append(
                (
                    node_id,
                    instance_id,
                )
            )

            return InputMediaObservation(
                node_id=node_id,
                instance_id=instance_id,
                service_id=service_id,
                path_name=path_name,
                observed_at=observed_at,
                container=None,
                video=VideoTrackObservation(
                    availability=EvidenceAvailability.AVAILABLE,
                    codec="h264",
                ),
                audio=None,
            )

    runtime = MediaObservationRuntime(
        profiles=(profile,),
        source_resolver=MediaObservationSourceResolver(
            rtsp_base_url="rtsp://media-node.internal:8554",
        ),
        observer=StubObserver(),
        stabilizer=MediaHealthStabilizer(
            degradation_seconds=10.0,
            recovery_seconds=5.0,
        ),
        operational_cycle_runtime=_InertOperationalCycleRuntime(),
    )

    result = runtime.run_once(
        node_id=node_id,
        instance_id=instance_id,
        observed_at=observed_at,
    )

    assert len(result.profiles) == 1

    assert observed_identity == [
        (
            node_id,
            instance_id,
        )
    ]

    assert (
        result.profiles[0].observation.node_id
        == node_id
    )
    assert (
        result.profiles[0].observation.instance_id
        == instance_id
    )

class _InertOperationalCycleRuntime:
    def process_cycle(
        self,
        *,
        node_id,
        instance_id,
        observation_result,
    ) -> None:
        return None


class _SchedulingObserver:
    """Observer unused by scheduling tests with empty profiles."""

    def observe(self, **kwargs):
        raise AssertionError(
            "observer must not be called with empty profiles"
        )


def test_run_forever_rejects_non_positive_interval() -> None:
    import asyncio

    runtime = MediaObservationRuntime(
        profiles=(),
        source_resolver=MediaObservationSourceResolver(
            rtsp_base_url="rtsp://media-node.internal:8554"
        ),
        observer=_SchedulingObserver(),
        stabilizer=MediaHealthStabilizer(
            degradation_seconds=10,
            recovery_seconds=5,
        ),
        operational_cycle_runtime=_InertOperationalCycleRuntime(),
    )

    observed_at = datetime(
        2026,
        9,
        22,
        18,
        0,
        tzinfo=timezone.utc,
    )

    node_id = NodeId(
        id="node-a",
        name="node-a",
        display_name="Node A",
        created_at=observed_at,
    )

    instance_id = NodeInstanceId(
        "instance-a"
    )

    async def scenario() -> None:
        with pytest.raises(
            ValueError,
            match=(
                "interval_seconds must be "
                "greater than zero"
            ),
        ):
            await runtime.run_forever(
                node_id=node_id,
                instance_id=instance_id,
                interval_seconds=0,
            )

    asyncio.run(scenario())


def test_run_forever_executes_run_once_off_event_loop(
    monkeypatch,
) -> None:
    import asyncio

    runtime = MediaObservationRuntime(
        profiles=(),
        source_resolver=MediaObservationSourceResolver(
            rtsp_base_url="rtsp://media-node.internal:8554"
        ),
        observer=_SchedulingObserver(),
        stabilizer=MediaHealthStabilizer(
            degradation_seconds=10,
            recovery_seconds=5,
        ),
        operational_cycle_runtime=_InertOperationalCycleRuntime(),
    )

    observed_at = datetime(
        2026,
        9,
        22,
        18,
        0,
        tzinfo=timezone.utc,
    )

    node_id = NodeId(
        id="node-a",
        name="node-a",
        display_name="Node A",
        created_at=observed_at,
    )

    instance_id = NodeInstanceId(
        "instance-a"
    )

    calls = []

    def fake_run_once(
        *,
        node_id,
        instance_id,
        observed_at,
    ):
        calls.append(
            (
                node_id,
                instance_id,
                observed_at,
            )
        )

        return MediaObservationRuntimeResult(
            observed_at=observed_at,
            profiles=(),
        )

    runtime.run_once = fake_run_once

    to_thread_calls = []

    async def fake_to_thread(
        function,
        /,
        *args,
        **kwargs,
    ):
        to_thread_calls.append(
            (
                function,
                args,
                kwargs,
            )
        )

        return function(
            *args,
            **kwargs,
        )

    sleep_calls = []

    async def fake_sleep(seconds):
        sleep_calls.append(seconds)
        raise asyncio.CancelledError

    monkeypatch.setattr(
        asyncio,
        "to_thread",
        fake_to_thread,
    )

    monkeypatch.setattr(
        asyncio,
        "sleep",
        fake_sleep,
    )

    async def scenario() -> None:
        with pytest.raises(
            asyncio.CancelledError
        ):
            await runtime.run_forever(
                node_id=node_id,
                instance_id=instance_id,
                interval_seconds=30.0,
            )

    asyncio.run(scenario())

    assert len(to_thread_calls) == 1
    assert len(calls) == 1

    called_node_id, called_instance_id, cycle_time = (
        calls[0]
    )

    assert called_node_id is node_id
    assert called_instance_id is instance_id
    assert cycle_time.tzinfo is not None

    assert sleep_calls == [30.0]




def test_run_once_forwards_complete_result_to_operational_cycle_runtime():
    observed_at = datetime(
        2026,
        9,
        22,
        19,
        0,
        tzinfo=timezone.utc,
    )

    node_id = NodeId(
        id="node-a",
        name="node-a",
        display_name="Node A",
        created_at=observed_at,
    )
    instance_id = NodeInstanceId(
        "streaming-primary"
    )

    profile = ExpectedMediaProfile(
        profile_id="impact-main",
        service_id="impact",
        path_name="impact",
        video=None,
        audio=None,
        container=None,
    )

    source_resolver = Mock()
    source_resolver.resolve.return_value = (
        "rtsp://127.0.0.1:8554/impact"
    )

    observation = InputMediaObservation(
        node_id=node_id,
        instance_id=instance_id,
        service_id="impact",
        path_name="impact",
        observed_at=observed_at,
        container=None,
        video=None,
        audio=None,
    )

    observer = Mock()
    observer.observe.return_value = observation

    stabilizer = Mock()
    stabilized_health = Mock()
    stabilizer.update.return_value = stabilized_health

    operational_cycle_runtime = Mock()

    runtime = MediaObservationRuntime(
        profiles=(profile,),
        source_resolver=source_resolver,
        observer=observer,
        stabilizer=stabilizer,
        operational_cycle_runtime=operational_cycle_runtime,
    )

    result = runtime.run_once(
        node_id=node_id,
        instance_id=instance_id,
        observed_at=observed_at,
    )

    operational_cycle_runtime.process_cycle.assert_called_once_with(
        node_id=node_id,
        instance_id=instance_id,
        observation_result=result,
    )


def test_run_once_propagates_operational_cycle_failure():
    observed_at = datetime(
        2026,
        9,
        22,
        19,
        5,
        tzinfo=timezone.utc,
    )

    node_id = NodeId(
        id="node-a",
        name="node-a",
        display_name="Node A",
        created_at=observed_at,
    )
    instance_id = NodeInstanceId(
        "streaming-primary"
    )

    profile = ExpectedMediaProfile(
        profile_id="impact-main",
        service_id="impact",
        path_name="impact",
        video=None,
        audio=None,
        container=None,
    )

    source_resolver = Mock()
    source_resolver.resolve.return_value = (
        "rtsp://127.0.0.1:8554/impact"
    )

    observation = InputMediaObservation(
        node_id=node_id,
        instance_id=instance_id,
        service_id="impact",
        path_name="impact",
        observed_at=observed_at,
        container=None,
        video=None,
        audio=None,
    )

    observer = Mock()
    observer.observe.return_value = observation

    stabilizer = Mock()
    stabilizer.update.return_value = Mock()

    operational_cycle_runtime = Mock()
    operational_cycle_runtime.process_cycle.side_effect = RuntimeError(
        "synthetic operational cycle failure"
    )

    runtime = MediaObservationRuntime(
        profiles=(profile,),
        source_resolver=source_resolver,
        observer=observer,
        stabilizer=stabilizer,
        operational_cycle_runtime=operational_cycle_runtime,
    )

    with pytest.raises(
        RuntimeError,
        match="synthetic operational cycle failure",
    ):
        runtime.run_once(
            node_id=node_id,
            instance_id=instance_id,
            observed_at=observed_at,
        )


def test_run_forever_retries_after_run_once_failure(
    monkeypatch,
) -> None:
    import asyncio

    runtime = MediaObservationRuntime(
        profiles=(),
        source_resolver=MediaObservationSourceResolver(
            rtsp_base_url="rtsp://media-node.internal:8554"
        ),
        observer=_SchedulingObserver(),
        stabilizer=MediaHealthStabilizer(
            degradation_seconds=10,
            recovery_seconds=5,
        ),
        operational_cycle_runtime=_InertOperationalCycleRuntime(),
    )

    observed_at = datetime(
        2026,
        9,
        26,
        1,
        40,
        tzinfo=timezone.utc,
    )

    node_id = NodeId(
        id="node-a",
        name="node-a",
        display_name="Node A",
        created_at=observed_at,
    )

    instance_id = NodeInstanceId(
        "instance-a"
    )

    calls = []

    def failing_then_cancelled_run_once(
        *,
        node_id,
        instance_id,
        observed_at,
    ):
        calls.append(observed_at)

        if len(calls) == 1:
            raise RuntimeError(
                "synthetic media observation failure"
            )

        raise asyncio.CancelledError

    runtime.run_once = failing_then_cancelled_run_once

    sleep_calls = []

    async def fake_sleep(seconds):
        sleep_calls.append(seconds)

    monkeypatch.setattr(
        asyncio,
        "sleep",
        fake_sleep,
    )

    async def scenario() -> None:
        with pytest.raises(
            asyncio.CancelledError
        ):
            await runtime.run_forever(
                node_id=node_id,
                instance_id=instance_id,
                interval_seconds=30.0,
            )

    asyncio.run(scenario())

    assert len(calls) == 2
    assert sleep_calls == [30.0]
