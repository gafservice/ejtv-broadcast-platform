"""Health transition to operational alarm mapping for the NOC.

ENG-013B — Node SDK

HealthTransitionAlarmFactory converts a classified NodeHealth
degradation into an immutable active AlarmRecord.

It does not persist alarms, acknowledge them, resolve them, close them,
evaluate health, or manage alarm lifecycle state.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

from app.noc.domain.node_alarm import (
    AlarmRecord,
    AlarmSeverity,
    AlarmState,
)
from app.noc.domain.node_health import NodeHealthState
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.services.health_transition_detector import (
    HealthTransition,
    HealthTransitionKind,
)


class HealthTransitionAlarmFactory:
    """Create active AlarmRecord objects from health degradations."""

    def create(
        self,
        *,
        transition: HealthTransition,
        source: NodeInstanceId,
        timestamp: datetime,
    ) -> AlarmRecord | None:
        """Create an alarm when a health transition requires attention."""

        if not isinstance(
            transition,
            HealthTransition,
        ):
            raise TypeError(
                "transition must be a HealthTransition"
            )

        if not isinstance(
            source,
            NodeInstanceId,
        ):
            raise TypeError(
                "source must be a NodeInstanceId"
            )

        self._validate_timestamp(
            timestamp
        )

        if (
            transition.kind
            is not HealthTransitionKind.DEGRADED
        ):
            return None

        severity = self._severity(
            transition.current.state
        )

        if severity is None:
            return None

        previous = transition.previous.state.value
        current = transition.current.state.value
        kind = transition.kind.value

        return AlarmRecord(
            alarm_id=self._alarm_id(),
            alarm_type="NODE_HEALTH_DEGRADED",
            severity=severity,
            state=AlarmState.ACTIVE,
            timestamp=timestamp,
            source=source,
            title=self._title(
                transition
            ),
            description=self._description(
                transition
            ),
            attributes={
                "previous": previous,
                "current": current,
                "transition": kind,
            },
        )

    @staticmethod
    def _alarm_id() -> str:
        """Create a unique operational alarm identifier."""

        return f"alm-{uuid4().hex}"

    @staticmethod
    def _severity(
        state: NodeHealthState,
    ) -> AlarmSeverity | None:
        """Map NodeHealth degradation state to alarm severity."""

        if state is NodeHealthState.CRITICAL:
            return AlarmSeverity.CRITICAL

        if state is NodeHealthState.DEGRADED:
            return AlarmSeverity.MAJOR

        if state is NodeHealthState.WARNING:
            return AlarmSeverity.WARNING

        return None

    @staticmethod
    def _title(
        transition: HealthTransition,
    ) -> str:
        """Build the operational alarm title."""

        return (
            "Node health degraded to "
            f"{transition.current.state.value}"
        )

    @staticmethod
    def _description(
        transition: HealthTransition,
    ) -> str:
        """Build the operational alarm description."""

        return (
            "Node health transitioned from "
            f"{transition.previous.state.value} "
            "to "
            f"{transition.current.state.value}"
        )

    @staticmethod
    def _validate_timestamp(
        timestamp: datetime,
    ) -> None:
        """Require an aware UTC timestamp."""

        if not isinstance(timestamp, datetime):
            raise TypeError(
                "timestamp must be a datetime"
            )

        if timestamp.tzinfo is None:
            raise ValueError(
                "timestamp must be timezone-aware and UTC"
            )

        offset = timestamp.utcoffset()

        if (
            offset is None
            or offset != timedelta(0)
        ):
            raise ValueError(
                "timestamp must be expressed in UTC"
            )
