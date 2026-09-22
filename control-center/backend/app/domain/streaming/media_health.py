"""Instantaneous Media Health derived from MediaEvaluation.

ENG-013C — Contract 4

This module converts descriptive media evaluation evidence into the
canonical operational HealthStatus vocabulary.

Contract 4 v1 is deliberately conservative:

- MATCH evidence supports HEALTHY;
- MISMATCH evidence produces DEGRADED;
- NOT_EVALUATED evidence produces UNKNOWN when no mismatch exists;
- CRITICAL is not produced by this contract version.

This module does not stabilize temporal state, detect transitions,
emit events or alarms, or persist runtime state.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.streaming.health import HealthStatus
from app.domain.streaming.media_evaluation import (
    MediaComparisonStatus,
    MediaComponentEvaluation,
    MediaEvaluation,
)


@dataclass(frozen=True, slots=True)
class MediaComponentHealth:
    """Instantaneous operational health of one evaluated media component."""

    component: str
    status: HealthStatus

    def __post_init__(self) -> None:
        component = self.component.strip()

        if not component:
            raise ValueError("component must not be blank")

        if not isinstance(self.status, HealthStatus):
            raise TypeError("status must be a HealthStatus")

        object.__setattr__(self, "component", component)


@dataclass(frozen=True, slots=True)
class MediaHealth:
    """Instantaneous aggregate health derived from one MediaEvaluation."""

    profile_id: str
    service_id: str
    path_name: str | None
    status: HealthStatus
    container: MediaComponentHealth | None = None
    video: MediaComponentHealth | None = None
    audio: MediaComponentHealth | None = None

    def __post_init__(self) -> None:
        profile_id = self.profile_id.strip()
        service_id = self.service_id.strip()

        if not profile_id:
            raise ValueError("profile_id must not be blank")

        if not service_id:
            raise ValueError("service_id must not be blank")

        path_name = self.path_name

        if path_name is not None:
            path_name = path_name.strip()

            if not path_name:
                raise ValueError(
                    "path_name must not be blank when provided"
                )

        if not isinstance(self.status, HealthStatus):
            raise TypeError("status must be a HealthStatus")

        for field_name in ("container", "video", "audio"):
            value = getattr(self, field_name)

            if (
                value is not None
                and not isinstance(value, MediaComponentHealth)
            ):
                raise TypeError(
                    f"{field_name} must be a "
                    "MediaComponentHealth or None"
                )

        object.__setattr__(self, "profile_id", profile_id)
        object.__setattr__(self, "service_id", service_id)
        object.__setattr__(self, "path_name", path_name)


class MediaHealthEvaluator:
    """Convert one MediaEvaluation into instantaneous MediaHealth."""

    def evaluate(
        self,
        *,
        evaluation: MediaEvaluation,
    ) -> MediaHealth:
        """Return instantaneous health without temporal stabilization."""

        if not isinstance(evaluation, MediaEvaluation):
            raise TypeError(
                "evaluation must be a MediaEvaluation"
            )

        container = self._evaluate_component(
            evaluation.container
        )
        video = self._evaluate_component(
            evaluation.video
        )
        audio = self._evaluate_component(
            evaluation.audio
        )

        status = self._aggregate_status(
            component.status
            for component in (
                container,
                video,
                audio,
            )
            if component is not None
        )

        return MediaHealth(
            profile_id=evaluation.profile_id,
            service_id=evaluation.service_id,
            path_name=evaluation.path_name,
            status=status,
            container=container,
            video=video,
            audio=audio,
        )

    @classmethod
    def _evaluate_component(
        cls,
        evaluation: MediaComponentEvaluation | None,
    ) -> MediaComponentHealth | None:
        if evaluation is None:
            return None

        statuses = (
            evaluation.presence_status,
            *(
                comparison.status
                for comparison in evaluation.comparisons
            ),
        )

        status = cls._status_from_comparisons(
            statuses
        )

        return MediaComponentHealth(
            component=evaluation.component,
            status=status,
        )

    @staticmethod
    def _status_from_comparisons(
        statuses,
    ) -> HealthStatus:
        statuses = tuple(statuses)

        if MediaComparisonStatus.MISMATCH in statuses:
            return HealthStatus.DEGRADED

        if MediaComparisonStatus.NOT_EVALUATED in statuses:
            return HealthStatus.UNKNOWN

        return HealthStatus.HEALTHY

    @staticmethod
    def _aggregate_status(
        statuses,
    ) -> HealthStatus:
        statuses = tuple(statuses)

        if not statuses:
            return HealthStatus.UNKNOWN

        if HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED

        if HealthStatus.UNKNOWN in statuses:
            return HealthStatus.UNKNOWN

        return HealthStatus.HEALTHY
