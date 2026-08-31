"""Critical multimedia path traffic evaluation for the NOC.

ENG-013B — Node SDK

CriticalPathTrafficEvaluator determines whether an enabled critical
multimedia path is currently carrying inbound traffic.

MediaMTXSnapshot is the source of truth for path/source operational
state. StreamingMeasurement is the source of truth for derived traffic
rates.

The evaluator is stateless. It does not calculate bitrate, apply grace
periods, maintain history, raise alarms or persist state.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.domain.streaming.metrics import (
    MeasurementQuality,
    StreamingMeasurement,
    StreamingPathMeasurement,
)
from app.domain.streaming.models import (
    MediaMTXSnapshot,
    MediaPath,
)
from app.noc.domain.critical_path_policy import (
    CriticalPathPolicy,
)


class CriticalPathTrafficState(str, Enum):
    """Current traffic condition of a critical multimedia path."""

    INACTIVE = "INACTIVE"
    UNKNOWN = "UNKNOWN"
    HEALTHY = "HEALTHY"
    STALLED = "STALLED"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class CriticalPathTrafficEvaluation:
    """Immutable traffic evaluation for one critical path."""

    policy: CriticalPathPolicy
    state: CriticalPathTrafficState
    media_path: MediaPath | None
    measurement: StreamingPathMeasurement | None

    def __post_init__(self) -> None:
        if not isinstance(self.policy, CriticalPathPolicy):
            raise TypeError(
                "policy must be a CriticalPathPolicy"
            )

        if not isinstance(
            self.state,
            CriticalPathTrafficState,
        ):
            raise TypeError(
                "state must be a CriticalPathTrafficState"
            )

        if (
            self.media_path is not None
            and not isinstance(self.media_path, MediaPath)
        ):
            raise TypeError(
                "media_path must be a MediaPath or None"
            )

        if (
            self.measurement is not None
            and not isinstance(
                self.measurement,
                StreamingPathMeasurement,
            )
        ):
            raise TypeError(
                "measurement must be a "
                "StreamingPathMeasurement or None"
            )

        if self.state is CriticalPathTrafficState.INACTIVE:
            return

        if self.media_path is None:
            raise ValueError(
                "non-INACTIVE traffic evaluation requires "
                "a media_path"
            )

        if not self.media_path.is_active:
            raise ValueError(
                "non-INACTIVE traffic evaluation requires "
                "an active media_path"
            )

        if not self.media_path.has_source:
            raise ValueError(
                "non-INACTIVE traffic evaluation requires "
                "a media source"
            )

        if not self.media_path.ready:
            raise ValueError(
                "non-INACTIVE traffic evaluation requires "
                "ready=True"
            )

        if not self.media_path.available:
            raise ValueError(
                "non-INACTIVE traffic evaluation requires "
                "available=True"
            )

        if not self.media_path.online:
            raise ValueError(
                "non-INACTIVE traffic evaluation requires "
                "online=True"
            )

        if self.state is CriticalPathTrafficState.UNKNOWN:
            return

        if self.measurement is None:
            raise ValueError(
                "HEALTHY/STALLED evaluation requires "
                "a measurement"
            )

        if (
            self.measurement.quality
            is not MeasurementQuality.AVAILABLE
        ):
            raise ValueError(
                "HEALTHY/STALLED evaluation requires "
                "an AVAILABLE measurement"
            )

        if self.measurement.name != self.policy.path:
            raise ValueError(
                "measurement path must match policy path"
            )

        bitrate = self.measurement.inbound_bitrate_bps

        if bitrate is None:
            raise ValueError(
                "AVAILABLE measurement requires inbound bitrate"
            )

        if self.state is CriticalPathTrafficState.HEALTHY:
            if bitrate <= 0:
                raise ValueError(
                    "HEALTHY evaluation requires positive "
                    "inbound bitrate"
                )

        if self.state is CriticalPathTrafficState.STALLED:
            if bitrate != 0:
                raise ValueError(
                    "STALLED evaluation requires zero "
                    "inbound bitrate"
                )


class CriticalPathTrafficEvaluator:
    """Evaluate critical-path inbound traffic health."""

    def evaluate(
        self,
        *,
        snapshot: MediaMTXSnapshot,
        measurement: StreamingMeasurement,
        policies: tuple[CriticalPathPolicy, ...],
    ) -> tuple[CriticalPathTrafficEvaluation, ...]:
        """Evaluate all enabled critical-path policies."""

        if not isinstance(snapshot, MediaMTXSnapshot):
            raise TypeError(
                "snapshot must be a MediaMTXSnapshot"
            )

        if not isinstance(
            measurement,
            StreamingMeasurement,
        ):
            raise TypeError(
                "measurement must be a StreamingMeasurement"
            )

        if not isinstance(policies, tuple):
            raise TypeError(
                "policies must be a tuple"
            )

        paths: set[str] = set()

        for policy in policies:
            if not isinstance(policy, CriticalPathPolicy):
                raise TypeError(
                    "policies must contain only "
                    "CriticalPathPolicy values"
                )

            if policy.path in paths:
                raise ValueError(
                    "policies must not contain duplicate "
                    "path values"
                )

            paths.add(policy.path)

        evaluations: list[
            CriticalPathTrafficEvaluation
        ] = []

        for policy in sorted(
            policies,
            key=lambda item: item.path,
        ):
            if not policy.enabled:
                continue

            media_path = snapshot.get_path(policy.path)
            path_measurement = measurement.get_path(
                policy.path
            )

            operational = (
                media_path is not None
                and media_path.is_active
                and media_path.has_source
                and media_path.ready
                and media_path.available
                and media_path.online
            )

            if not operational:
                state = CriticalPathTrafficState.INACTIVE

            elif (
                path_measurement is None
                or path_measurement.quality
                is not MeasurementQuality.AVAILABLE
                or path_measurement.inbound_bitrate_bps
                is None
            ):
                state = CriticalPathTrafficState.UNKNOWN

            elif path_measurement.inbound_bitrate_bps > 0:
                state = CriticalPathTrafficState.HEALTHY

            else:
                state = CriticalPathTrafficState.STALLED

            evaluations.append(
                CriticalPathTrafficEvaluation(
                    policy=policy,
                    state=state,
                    media_path=media_path,
                    measurement=path_measurement,
                )
            )

        return tuple(evaluations)
