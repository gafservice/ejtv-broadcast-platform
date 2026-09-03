"""Historical alarm lifecycle transitions for the NOC.

ENG-013B — Operational History

AlarmRecord represents the current canonical state of an operational
alarm. AlarmTransition represents an immutable historical fact describing
a lifecycle transition of that alarm.

Historical transition types are intentionally separate from AlarmState.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import hashlib
from types import MappingProxyType
from typing import Mapping

from app.noc.domain.node_alarm import AlarmState
from app.noc.domain.node_instance import NodeInstanceId


class AlarmTransitionType(str, Enum):
    """Canonical historical alarm transition types."""

    OPENED = "OPENED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    INVALIDATED = "INVALIDATED"
    CARRIED_FORWARD = "CARRIED_FORWARD"
    RECOVERED_AT_STARTUP = "RECOVERED_AT_STARTUP"

    def __str__(self) -> str:
        return self.value


def make_alarm_transition_id(
    *,
    alarm_id: str,
    transition_type: AlarmTransitionType,
    timestamp: datetime,
    source: NodeInstanceId,
    state: AlarmState,
) -> str:
    """Return the deterministic identity of one lifecycle transition."""

    normalized_alarm_id = AlarmTransition._normalize_required(
        alarm_id,
        "alarm_id",
    )

    if not isinstance(
        transition_type,
        AlarmTransitionType,
    ):
        raise TypeError(
            "transition_type must be an AlarmTransitionType"
        )

    AlarmTransition._validate_utc_datetime(
        timestamp
    )

    if not isinstance(source, NodeInstanceId):
        raise TypeError(
            "source must be a NodeInstanceId"
        )

    if not isinstance(state, AlarmState):
        raise TypeError(
            "state must be an AlarmState"
        )

    canonical_timestamp = timestamp.isoformat(
        timespec="microseconds"
    )

    payload = "\0".join(
        (
            normalized_alarm_id,
            transition_type.value,
            canonical_timestamp,
            source.value,
            state.value,
        )
    )

    digest = hashlib.sha256(
        payload.encode("utf-8")
    ).hexdigest()

    return f"alarm-transition:{digest}"


@dataclass(frozen=True, slots=True)
class AlarmTransition:
    """Immutable historical fact for one alarm lifecycle transition."""

    transition_id: str
    alarm_id: str
    transition_type: AlarmTransitionType
    timestamp: datetime
    source: NodeInstanceId
    state: AlarmState

    actor: str | None = None
    metadata: Mapping[str, str] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "transition_id",
            self._normalize_required(
                self.transition_id,
                "transition_id",
            ),
        )

        object.__setattr__(
            self,
            "alarm_id",
            self._normalize_required(
                self.alarm_id,
                "alarm_id",
            ),
        )

        if not isinstance(
            self.transition_type,
            AlarmTransitionType,
        ):
            raise TypeError(
                "AlarmTransition.transition_type must be "
                "an AlarmTransitionType"
            )

        if not isinstance(self.source, NodeInstanceId):
            raise TypeError(
                "AlarmTransition.source must be a NodeInstanceId"
            )

        if not isinstance(self.state, AlarmState):
            raise TypeError(
                "AlarmTransition.state must be an AlarmState"
            )

        self._validate_utc_datetime(self.timestamp)

        if self.actor is not None:
            object.__setattr__(
                self,
                "actor",
                self._normalize_optional(
                    self.actor,
                    "actor",
                ),
            )

        if self.metadata is not None:
            normalized: dict[str, str] = {}

            for key, value in self.metadata.items():
                if not isinstance(key, str):
                    raise TypeError(
                        "AlarmTransition.metadata keys must be strings"
                    )

                if not isinstance(value, str):
                    raise TypeError(
                        "AlarmTransition.metadata values must be strings"
                    )

                normalized_key = key.strip()
                normalized_value = value.strip()

                if not normalized_key:
                    raise ValueError(
                        "AlarmTransition.metadata keys must not be empty"
                    )

                normalized[normalized_key] = normalized_value

            object.__setattr__(
                self,
                "metadata",
                MappingProxyType(normalized),
            )

    @staticmethod
    def _normalize_required(
        value: str,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise TypeError(
                f"AlarmTransition.{field_name} must be a string"
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                f"AlarmTransition.{field_name} must not be empty"
            )

        return normalized

    @staticmethod
    def _normalize_optional(
        value: str,
        field_name: str,
    ) -> str | None:
        if not isinstance(value, str):
            raise TypeError(
                f"AlarmTransition.{field_name} must be a string"
            )

        normalized = value.strip()

        return normalized or None

    @staticmethod
    def _validate_utc_datetime(value: datetime) -> None:
        if not isinstance(value, datetime):
            raise TypeError(
                "AlarmTransition.timestamp must be a datetime"
            )

        if value.tzinfo is None:
            raise ValueError(
                "AlarmTransition.timestamp must be "
                "timezone-aware and UTC"
            )

        offset = value.utcoffset()

        if offset is None or offset != timedelta(0):
            raise ValueError(
                "AlarmTransition.timestamp must be expressed in UTC"
            )
