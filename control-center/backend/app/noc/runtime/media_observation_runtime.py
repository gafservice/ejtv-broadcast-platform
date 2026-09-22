"""Automatic media observation runtime.

ENG-013C — Media Health

This runtime coordinates the already-defined media contracts:

ExpectedMediaProfile
    -> physical observation source
    -> InputMediaObservation
    -> MediaEvaluation
    -> instantaneous MediaHealth
    -> stabilized MediaHealth

It owns the Media Health scheduling loop, but intentionally does not own
persistence, events, alarms, dashboard rendering or runtime process ownership.
"""

from __future__ import annotations

import asyncio

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from app.domain.streaming.expected_media_profile import (
    ExpectedMediaProfile,
)
from app.domain.streaming.media_evaluation import (
    MediaEvaluation,
    MediaEvaluator,
)
from app.domain.streaming.media_health import (
    MediaHealth,
    MediaHealthEvaluator,
)
from app.domain.streaming.media_observation import (
    InputMediaObservation,
)
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.services.media_observation_source_resolver import (
    MediaObservationSourceResolver,
)
from app.services.media_health_stabilizer import (
    MediaHealthStabilizer,
)


class MediaObserver(Protocol):
    """Boundary required by MediaObservationRuntime."""

    def observe(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        service_id: str,
        source: str,
        observed_at: datetime,
        path_name: str | None = None,
    ) -> InputMediaObservation:
        ...


@dataclass(frozen=True, slots=True)
class MediaObservationRuntimeProfileResult:
    """Result of one complete media-health chain for one profile."""

    profile: ExpectedMediaProfile
    source: str
    observation: InputMediaObservation
    evaluation: MediaEvaluation
    instantaneous_health: MediaHealth
    stabilized_health: MediaHealth


@dataclass(frozen=True, slots=True)
class MediaObservationRuntimeResult:
    """Result of one automatic media observation cycle."""

    observed_at: datetime
    profiles: tuple[
        MediaObservationRuntimeProfileResult,
        ...,
    ]



class MediaOperationalCycleProcessor(Protocol):
    """Operational consumer of one completed media cycle."""

    def process_cycle(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        observation_result: MediaObservationRuntimeResult,
    ) -> None:
        ...


class MediaObservationRuntime:
    """Coordinate one automatic media observation cycle."""

    def __init__(
        self,
        *,
        profiles: tuple[ExpectedMediaProfile, ...],
        source_resolver: MediaObservationSourceResolver,
        observer: MediaObserver,
        stabilizer: MediaHealthStabilizer,
        operational_cycle_runtime: MediaOperationalCycleProcessor,
    ) -> None:
        self._profiles = profiles
        self._source_resolver = source_resolver
        self._observer = observer
        self._stabilizer = stabilizer
        self._operational_cycle_runtime = operational_cycle_runtime

        self._media_evaluator = MediaEvaluator()
        self._health_evaluator = MediaHealthEvaluator()

    async def run_forever(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        interval_seconds: float,
    ) -> None:
        """Continuously execute physical Media Health cycles."""

        if interval_seconds <= 0:
            raise ValueError(
                "interval_seconds must be greater than zero"
            )

        while True:
            observed_at = datetime.now(timezone.utc)

            await asyncio.to_thread(
                self.run_once,
                node_id=node_id,
                instance_id=instance_id,
                observed_at=observed_at,
            )

            await asyncio.sleep(interval_seconds)

    def run_once(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        observed_at: datetime,
    ) -> MediaObservationRuntimeResult:
        """Run one complete media-health cycle."""

        results: list[
            MediaObservationRuntimeProfileResult
        ] = []

        for profile in self._profiles:
            if profile.path_name is None:
                continue

            source = self._source_resolver.resolve(
                path_name=profile.path_name,
            )

            observation = self._observer.observe(
                node_id=node_id,
                instance_id=instance_id,
                service_id=profile.service_id,
                source=source,
                observed_at=observed_at,
                path_name=profile.path_name,
            )

            evaluation = self._media_evaluator.evaluate(
                profile=profile,
                observation=observation,
            )

            instantaneous_health = (
                self._health_evaluator.evaluate(
                    evaluation=evaluation,
                )
            )

            stabilized_health = self._stabilizer.stabilize(
                health=instantaneous_health,
                observed_at=observed_at,
            )

            results.append(
                MediaObservationRuntimeProfileResult(
                    profile=profile,
                    source=source,
                    observation=observation,
                    evaluation=evaluation,
                    instantaneous_health=instantaneous_health,
                    stabilized_health=stabilized_health,
                )
            )

        result = MediaObservationRuntimeResult(
            observed_at=observed_at,
            profiles=tuple(results),
        )

        self._operational_cycle_runtime.process_cycle(
            node_id=node_id,
            instance_id=instance_id,
            observation_result=result,
        )

        return result
