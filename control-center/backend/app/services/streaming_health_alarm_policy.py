"""Alarm policy for semantic StreamingHealth transitions.

ENG-013B — Stream Health Contract Block 5

This module decides what alarm lifecycle action is justified by an
already-detected StreamingHealth transition.

It does not:

- evaluate Stream Health;
- stabilize Stream Health;
- detect transitions;
- create AlarmRecord objects;
- persist alarms;
- execute AlarmService lifecycle operations.

The initial policy is intentionally conservative.  Health severity
alone is not sufficient evidence to open an operator-facing alarm.
Richer policy inputs such as role, scope, impact, expected presence and
affected population belong to later Stream Health contract blocks.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.domain.streaming.health import HealthStatus
from app.noc.services.health_transition_detector import (
    HealthTransitionKind,
)
from app.services.streaming_health_transition_detector import (
    StreamingHealthTransition,
)


class StreamingHealthAlarmAction(StrEnum):
    """Alarm lifecycle action requested by Stream Health policy."""

    NONE = "NONE"
    RAISE = "RAISE"
    KEEP = "KEEP"
    RESOLVE = "RESOLVE"


@dataclass(frozen=True, slots=True)
class StreamingHealthAlarmDecision:
    """Immutable result of one Stream Health alarm-policy evaluation."""

    action: StreamingHealthAlarmAction
    transition: StreamingHealthTransition | None

    def __post_init__(self) -> None:
        if not isinstance(
            self.action,
            StreamingHealthAlarmAction,
        ):
            raise TypeError(
                "action must be a StreamingHealthAlarmAction"
            )

        if (
            self.transition is not None
            and not isinstance(
                self.transition,
                StreamingHealthTransition,
            )
        ):
            raise TypeError(
                "transition must be a "
                "StreamingHealthTransition or None"
            )


class StreamingHealthAlarmPolicy:
    """Decide alarm lifecycle intent from one semantic transition."""

    def evaluate(
        self,
        *,
        transition: StreamingHealthTransition | None,
    ) -> StreamingHealthAlarmDecision:
        """Return the justified alarm action for the transition."""

        if (
            transition is not None
            and not isinstance(
                transition,
                StreamingHealthTransition,
            )
        ):
            raise TypeError(
                "transition must be a "
                "StreamingHealthTransition or None"
            )

        if transition is None:
            return StreamingHealthAlarmDecision(
                action=StreamingHealthAlarmAction.NONE,
                transition=None,
            )

        current_status = transition.current.status

        if (
            transition.kind is HealthTransitionKind.RECOVERED
            and current_status is HealthStatus.HEALTHY
        ):
            return StreamingHealthAlarmDecision(
                action=StreamingHealthAlarmAction.RESOLVE,
                transition=transition,
            )

        if transition.kind is HealthTransitionKind.IMPROVED:
            return StreamingHealthAlarmDecision(
                action=StreamingHealthAlarmAction.KEEP,
                transition=transition,
            )

        if (
            transition.kind is HealthTransitionKind.UNKNOWN
            and transition.previous.status
            in (
                HealthStatus.DEGRADED,
                HealthStatus.CRITICAL,
            )
        ):
            return StreamingHealthAlarmDecision(
                action=StreamingHealthAlarmAction.KEEP,
                transition=transition,
            )

        return StreamingHealthAlarmDecision(
            action=StreamingHealthAlarmAction.NONE,
            transition=transition,
        )
