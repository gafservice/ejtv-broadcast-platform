"""Daily continuity service for durable NOC alarms.

ENG-013B — persistent operational history.

Active or acknowledged alarms that survive across a UTC day boundary
receive one deterministic CARRIED_FORWARD transition at 00:00:00 UTC.

The alarm identity and canonical AlarmRecord are preserved.  The
transition is historical evidence of continuity, not a new alarm state.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone

from app.noc.domain.node_alarm import AlarmRecord, AlarmState
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.history.alarm_transition import (
    AlarmTransition,
    AlarmTransitionType,
    make_alarm_transition_id,
)
from app.noc.history.evidence_writer import EvidenceWriter
from app.noc.history.repository import AlarmHistoryRepository


@dataclass(frozen=True, slots=True)
class DailyAlarmContinuityResult:
    """Summary of one daily continuity execution."""

    carried_forward: tuple[AlarmTransition, ...]

    @property
    def carried_forward_count(self) -> int:
        return len(self.carried_forward)


class DailyAlarmContinuityService:
    """Record daily continuity for alarms requiring attention."""

    def __init__(
        self,
        history_repository: AlarmHistoryRepository,
        evidence_writer: EvidenceWriter | None = None,
    ) -> None:
        if not isinstance(
            history_repository,
            AlarmHistoryRepository,
        ):
            raise TypeError(
                "history_repository must implement "
                "AlarmHistoryRepository"
            )

        if (
            evidence_writer is not None
            and not isinstance(
                evidence_writer,
                EvidenceWriter,
            )
        ):
            raise TypeError(
                "evidence_writer must implement EvidenceWriter"
            )

        self._history_repository = history_repository
        self._evidence_writer = evidence_writer

    def carry_forward(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        day: date,
    ) -> DailyAlarmContinuityResult:
        """Record alarms surviving into ``day`` at midnight UTC."""

        if not isinstance(node_id, NodeId):
            raise TypeError("node_id must be a NodeId")

        if not isinstance(instance_id, NodeInstanceId):
            raise TypeError(
                "instance_id must be a NodeInstanceId"
            )

        if not isinstance(day, date):
            raise TypeError("day must be a date")

        boundary = datetime.combine(
            day,
            time.min,
            tzinfo=timezone.utc,
        )

        alarms = self._history_repository.list_active(
            node_id=node_id,
            instance_id=instance_id,
        )

        carried: list[AlarmTransition] = []

        for alarm in alarms:
            if alarm.timestamp >= boundary:
                continue

            transition = self._make_transition(
                alarm=alarm,
                instance_id=instance_id,
                boundary=boundary,
            )

            self._history_repository.record_lifecycle(
                node_id=node_id,
                instance_id=instance_id,
                alarm=alarm,
                transition=transition,
            )

            if self._evidence_writer is not None:
                self._evidence_writer.append_alarm_transition(
                    transition
                )

            carried.append(transition)

        return DailyAlarmContinuityResult(
            carried_forward=tuple(carried)
        )

    def catch_up(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        through: datetime,
    ) -> DailyAlarmContinuityResult:
        """Reconstruct UTC day boundaries from durable history.

        The state at each boundary is derived from immutable lifecycle
        transitions strictly before that boundary. Historical continuity
        is appended without mutating the current canonical AlarmRecord.
        """

        if not isinstance(node_id, NodeId):
            raise TypeError("node_id must be a NodeId")

        if not isinstance(instance_id, NodeInstanceId):
            raise TypeError(
                "instance_id must be a NodeInstanceId"
            )

        if not isinstance(through, datetime):
            raise TypeError(
                "through must be a datetime"
            )

        if (
            through.tzinfo is None
            or through.utcoffset() is None
        ):
            raise ValueError(
                "through must be timezone-aware"
            )

        through_utc = through.astimezone(
            timezone.utc
        )

        alarms = self._history_repository.list_all(
            node_id=node_id,
            instance_id=instance_id,
        )

        carried: list[AlarmTransition] = []

        for alarm in alarms:
            opened_at = alarm.timestamp.astimezone(
                timezone.utc
            )

            transitions = (
                self._history_repository.list_transitions(
                    alarm.alarm_id
                )
            )

            day = (
                opened_at.date()
                + timedelta(days=1)
            )

            last_day = through_utc.date()

            while day <= last_day:
                boundary = datetime.combine(
                    day,
                    time.min,
                    tzinfo=timezone.utc,
                )

                state = self._state_at_boundary(
                    transitions=transitions,
                    boundary=boundary,
                )

                if state is None:
                    state = self._legacy_state_at_boundary(
                        alarm=alarm,
                        transitions=transitions,
                        boundary=boundary,
                    )

                if state not in {
                    AlarmState.ACTIVE,
                    AlarmState.ACKNOWLEDGED,
                }:
                    day += timedelta(days=1)
                    continue

                transition = self._make_transition(
                    alarm=alarm,
                    instance_id=instance_id,
                    boundary=boundary,
                    state=state,
                )

                self._history_repository.record_historical_transition(
                    node_id=node_id,
                    instance_id=instance_id,
                    transition=transition,
                )

                if self._evidence_writer is not None:
                    self._evidence_writer.append_alarm_transition(
                        transition
                    )

                carried.append(transition)

                day += timedelta(days=1)

        return DailyAlarmContinuityResult(
            carried_forward=tuple(carried)
        )

    @staticmethod
    def _legacy_state_at_boundary(
        *,
        alarm: AlarmRecord,
        transitions: tuple[AlarmTransition, ...],
        boundary: datetime,
    ) -> AlarmState | None:
        """Fallback for pre-ledger durable alarm records.

        The current AlarmRecord may be used only when no authoritative
        lifecycle transition exists. Evidence-only transitions such as
        CARRIED_FORWARD and RECOVERED_AT_STARTUP do not disable this
        compatibility path.
        """

        lifecycle_types = {
            AlarmTransitionType.OPENED,
            AlarmTransitionType.ACKNOWLEDGED,
            AlarmTransitionType.RESOLVED,
            AlarmTransitionType.CLOSED,
        }

        if any(
            transition.transition_type in lifecycle_types
            for transition in transitions
        ):
            return None

        opened_at = alarm.timestamp.astimezone(
            timezone.utc
        )

        if opened_at >= boundary:
            return None

        if alarm.state in {
            AlarmState.ACTIVE,
            AlarmState.ACKNOWLEDGED,
        }:
            return alarm.state

        return None

    @staticmethod
    def _state_at_boundary(
        *,
        transitions: tuple[AlarmTransition, ...],
        boundary: datetime,
    ) -> AlarmState | None:
        """Return canonical alarm state immediately before boundary."""

        state: AlarmState | None = None

        for transition in transitions:
            if transition.timestamp >= boundary:
                break

            transition_type = transition.transition_type

            if transition_type is AlarmTransitionType.OPENED:
                state = AlarmState.ACTIVE

            elif (
                transition_type
                is AlarmTransitionType.ACKNOWLEDGED
            ):
                state = AlarmState.ACKNOWLEDGED

            elif (
                transition_type
                is AlarmTransitionType.RESOLVED
            ):
                state = AlarmState.RESOLVED

            elif (
                transition_type
                is AlarmTransitionType.CLOSED
            ):
                state = AlarmState.CLOSED

            elif transition_type in {
                AlarmTransitionType.CARRIED_FORWARD,
                AlarmTransitionType.RECOVERED_AT_STARTUP,
            }:
                # Evidence-only transitions do not create a lifecycle
                # change. Their state documents the already-current state.
                continue

        return state

    @staticmethod
    def _make_transition(
        *,
        alarm: AlarmRecord,
        instance_id: NodeInstanceId,
        boundary: datetime,
        state: AlarmState | None = None,
    ) -> AlarmTransition:
        transition_type = (
            AlarmTransitionType.CARRIED_FORWARD
        )

        transition_state = (
            alarm.state
            if state is None
            else state
        )

        transition_id = make_alarm_transition_id(
            alarm_id=alarm.alarm_id,
            transition_type=transition_type,
            timestamp=boundary,
            source=instance_id,
            state=transition_state,
        )

        return AlarmTransition(
            transition_id=transition_id,
            alarm_id=alarm.alarm_id,
            transition_type=transition_type,
            timestamp=boundary,
            source=instance_id,
            state=transition_state,
            actor=None,
            metadata=alarm.attributes,
        )
