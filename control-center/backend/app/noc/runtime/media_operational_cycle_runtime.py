"""Operational coordination for one complete Media Health cycle.

MediaOperationalCycleRuntime consumes the already observed, evaluated and
stabilized result of one MediaObservationRuntime cycle.

It forwards each stabilized MediaHealth value, in profile order, to the
MediaOperationalRuntime.

The coordinator does not observe media, evaluate expectations, stabilize
health, detect transitions, persist events, own alarms, or implement retry
policy.

Processing is intentionally fail-fast: if one profile raises, the exception
is propagated and later profiles in that cycle are not processed.
"""

from __future__ import annotations

from app.noc.current_state.media_health_current_state import (
    MediaHealthCurrentState,
    MediaHealthCurrentStateRepository,
)
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.runtime.media_observation_runtime import (
    MediaObservationRuntimeResult,
)
from app.noc.runtime.media_operational_runtime import (
    MediaOperationalRuntime,
)


class MediaOperationalCycleRuntime:
    """Coordinate operational processing for one Media observation cycle."""

    def __init__(
        self,
        *,
        operational_runtime: MediaOperationalRuntime,
        current_state_repository: MediaHealthCurrentStateRepository,
    ) -> None:
        if not isinstance(
            operational_runtime,
            MediaOperationalRuntime,
        ):
            raise TypeError(
                "operational_runtime must be a "
                "MediaOperationalRuntime"
            )

        if not isinstance(
            current_state_repository,
            MediaHealthCurrentStateRepository,
        ):
            raise TypeError(
                "current_state_repository must implement "
                "MediaHealthCurrentStateRepository"
            )

        self._operational_runtime = operational_runtime
        self._current_state_repository = current_state_repository

    @property
    def operational_runtime(
        self,
    ) -> MediaOperationalRuntime:
        return self._operational_runtime

    def process_cycle(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        observation_result: MediaObservationRuntimeResult,
    ) -> None:
        """Process stabilized Media Health values in profile order."""

        if not isinstance(node_id, NodeId):
            raise TypeError(
                "node_id must be a NodeId"
            )

        if not isinstance(
            instance_id,
            NodeInstanceId,
        ):
            raise TypeError(
                "instance_id must be a NodeInstanceId"
            )

        if not isinstance(
            observation_result,
            MediaObservationRuntimeResult,
        ):
            raise TypeError(
                "observation_result must be a "
                "MediaObservationRuntimeResult"
            )

        for profile_result in observation_result.profiles:
            health = profile_result.stabilized_health

            self._current_state_repository.save(
                state=MediaHealthCurrentState(
                    profile_id=health.profile_id,
                    service_id=health.service_id,
                    path_name=health.path_name,
                    observed_at=observation_result.observed_at,
                    health=health,
                )
            )

            self._operational_runtime.process_health(
                node_id=node_id,
                instance_id=instance_id,
                health=health,
                observed_at=observation_result.observed_at,
            )
