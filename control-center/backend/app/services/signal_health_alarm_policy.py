"""Alarm lifecycle policy for Signal Health transitions.

ENG-013C — Signal Health -> Alarms / Recovery

The policy consumes one already-detected SignalHealthTransition and decides
only the alarm lifecycle action.

It does not:

- evaluate Signal Health;
- evaluate Media Health;
- evaluate Source Transport Health;
- detect or reclassify transitions;
- create or persist alarms;
- inspect existing alarms;
- interact with AlarmService.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.domain.streaming.health import HealthStatus
from app.noc.services.health_transition_detector import (
    HealthTransitionKind,
)
from app.services.signal_health_transition_detector import (
    SignalHealthTransition,
)


class SignalHealthAlarmAction(str, Enum):
    """Lifecycle action authorized by Signal Health alarm policy."""

    NONE = "NONE"
    RAISE = "RAISE"
    KEEP = "KEEP"
    RESOLVE = "RESOLVE"


@dataclass(frozen=True, slots=True)
class SignalHealthAlarmDecision:
    """Immutable result of one Signal Health alarm policy evaluation."""

    action: SignalHealthAlarmAction
    transition: SignalHealthTransition | None

    def __post_init__(self) -> None:
        if not isinstance(
            self.action,
            SignalHealthAlarmAction,
        ):
            raise TypeError(
                "action must be a SignalHealthAlarmAction"
            )

        if (
            self.transition is not None
            and not isinstance(
                self.transition,
                SignalHealthTransition,
            )
        ):
            raise TypeError(
                "transition must be a "
                "SignalHealthTransition or None"
            )


class SignalHealthAlarmPolicy:
    """Map Signal Health transitions to alarm lifecycle actions."""

    def evaluate(
        self,
        *,
        transition: SignalHealthTransition | None,
    ) -> SignalHealthAlarmDecision:
        if (
            transition is not None
            and not isinstance(
                transition,
                SignalHealthTransition,
            )
        ):
            raise TypeError(
                "transition must be a "
                "SignalHealthTransition or None"
            )

        if transition is None:
            return SignalHealthAlarmDecision(
                action=SignalHealthAlarmAction.NONE,
                transition=None,
            )

        if transition.kind is HealthTransitionKind.UNKNOWN:
            action = (
                SignalHealthAlarmAction.RESOLVE
                if transition.current.status is HealthStatus.HEALTHY
                else SignalHealthAlarmAction.KEEP
            )

        elif transition.kind is HealthTransitionKind.RECOVERED:
            action = SignalHealthAlarmAction.RESOLVE

        elif transition.kind is HealthTransitionKind.IMPROVED:
            action = SignalHealthAlarmAction.KEEP

        elif transition.kind is HealthTransitionKind.DEGRADED:
            action = self._degraded_action(
                transition
            )

        else:
            raise ValueError(
                "unsupported Signal Health transition kind: "
                f"{transition.kind}"
            )

        return SignalHealthAlarmDecision(
            action=action,
            transition=transition,
        )

    @staticmethod
    def _degraded_action(
        transition: SignalHealthTransition,
    ) -> SignalHealthAlarmAction:
        previous_status = transition.previous.status
        current_status = transition.current.status

        if (
            previous_status is HealthStatus.HEALTHY
            and current_status
            in (
                HealthStatus.DEGRADED,
                HealthStatus.CRITICAL,
            )
        ):
            return SignalHealthAlarmAction.RAISE

        if (
            previous_status is HealthStatus.DEGRADED
            and current_status is HealthStatus.CRITICAL
        ):
            return SignalHealthAlarmAction.KEEP

        raise ValueError(
            "unsupported DEGRADED Signal Health transition: "
            f"{previous_status.value} -> "
            f"{current_status.value}"
        )
