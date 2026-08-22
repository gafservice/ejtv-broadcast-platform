"""Runtime orchestration for multimedia session alarms.

ENG-013B — Node SDK

SessionAlarmRuntime coordinates the operational multimedia-session
alarm pipelines:

- expected multimedia sessions;
- reconnect flapping;
- critical paths without readers.

The runtime owns orchestration only. Domain interpretation, temporal
stabilization and alarm lifecycle remain delegated to their respective
components.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from app.domain.sessions import SessionSnapshot
from app.noc.domain.critical_path_policy import CriticalPathPolicy
from app.noc.domain.expected_session_policy import ExpectedSessionPolicy
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.services.critical_path_no_readers_alarm_service import (
    CriticalPathNoReadersAlarmResult,
    CriticalPathNoReadersAlarmService,
)
from app.noc.services.critical_path_reader_evaluator import (
    CriticalPathReaderEvaluator,
)
from app.noc.services.critical_path_reader_stabilizer import (
    CriticalPathReaderStabilizer,
)
from app.noc.services.expected_session_alarm_service import (
    ExpectedSessionAlarmResult,
    ExpectedSessionAlarmService,
)
from app.noc.services.expected_session_evaluator import (
    ExpectedSessionEvaluator,
)
from app.noc.services.expected_session_stabilizer import (
    ExpectedSessionStabilizer,
)
from app.noc.services.reconnect_flapping_alarm_service import (
    ReconnectFlappingAlarmResult,
    ReconnectFlappingAlarmService,
)
from app.noc.services.reconnect_flapping_evaluator import (
    ReconnectFlappingEvaluator,
)
from app.noc.services.session_transition_detector import (
    SessionTransition,
)


@dataclass(frozen=True, slots=True)
class SessionAlarmRuntimeResult:
    """Immutable result of one multimedia alarm runtime cycle."""

    expected_session_results: tuple[
        ExpectedSessionAlarmResult,
        ...,
    ]
    reconnect_flapping_results: tuple[
        ReconnectFlappingAlarmResult,
        ...,
    ]
    critical_path_results: tuple[
        CriticalPathNoReadersAlarmResult,
        ...,
    ]


class SessionAlarmRuntime:
    """Coordinate multimedia-session operational alarm pipelines."""

    def __init__(
        self,
        *,
        expected_session_alarm_service: ExpectedSessionAlarmService,
        reconnect_flapping_alarm_service: ReconnectFlappingAlarmService,
        critical_path_alarm_service: CriticalPathNoReadersAlarmService,
        expected_session_policies: tuple[
            ExpectedSessionPolicy,
            ...,
        ] = (),
        critical_path_policies: tuple[
            CriticalPathPolicy,
            ...,
        ] = (),
        expected_session_evaluator: ExpectedSessionEvaluator | None = None,
        expected_session_stabilizer: ExpectedSessionStabilizer | None = None,
        reconnect_flapping_evaluator: ReconnectFlappingEvaluator | None = None,
        critical_path_evaluator: CriticalPathReaderEvaluator | None = None,
        critical_path_stabilizer: CriticalPathReaderStabilizer | None = None,
        reconnect_flapping_enabled: bool = True,
    ) -> None:
        if not isinstance(
            expected_session_alarm_service,
            ExpectedSessionAlarmService,
        ):
            raise TypeError(
                "expected_session_alarm_service must be an "
                "ExpectedSessionAlarmService"
            )

        if not isinstance(
            reconnect_flapping_alarm_service,
            ReconnectFlappingAlarmService,
        ):
            raise TypeError(
                "reconnect_flapping_alarm_service must be a "
                "ReconnectFlappingAlarmService"
            )

        if not isinstance(
            critical_path_alarm_service,
            CriticalPathNoReadersAlarmService,
        ):
            raise TypeError(
                "critical_path_alarm_service must be a "
                "CriticalPathNoReadersAlarmService"
            )

        if not isinstance(expected_session_policies, tuple):
            raise TypeError(
                "expected_session_policies must be a tuple"
            )

        for policy in expected_session_policies:
            if not isinstance(policy, ExpectedSessionPolicy):
                raise TypeError(
                    "expected_session_policies must contain only "
                    "ExpectedSessionPolicy values"
                )

        if not isinstance(critical_path_policies, tuple):
            raise TypeError(
                "critical_path_policies must be a tuple"
            )

        for policy in critical_path_policies:
            if not isinstance(policy, CriticalPathPolicy):
                raise TypeError(
                    "critical_path_policies must contain only "
                    "CriticalPathPolicy values"
                )

        self._expected_session_alarm_service = (
            expected_session_alarm_service
        )
        self._reconnect_flapping_alarm_service = (
            reconnect_flapping_alarm_service
        )
        self._critical_path_alarm_service = (
            critical_path_alarm_service
        )

        self._expected_session_policies = (
            expected_session_policies
        )
        self._critical_path_policies = (
            critical_path_policies
        )

        self._expected_session_evaluator = (
            expected_session_evaluator
            if expected_session_evaluator is not None
            else ExpectedSessionEvaluator()
        )
        self._expected_session_stabilizer = (
            expected_session_stabilizer
            if expected_session_stabilizer is not None
            else ExpectedSessionStabilizer()
        )
        self._reconnect_flapping_evaluator = (
            reconnect_flapping_evaluator
            if reconnect_flapping_evaluator is not None
            else ReconnectFlappingEvaluator()
        )
        self._critical_path_evaluator = (
            critical_path_evaluator
            if critical_path_evaluator is not None
            else CriticalPathReaderEvaluator()
        )
        self._critical_path_stabilizer = (
            critical_path_stabilizer
            if critical_path_stabilizer is not None
            else CriticalPathReaderStabilizer()
        )

        if not isinstance(
            reconnect_flapping_enabled,
            bool,
        ):
            raise TypeError(
                "reconnect_flapping_enabled must be a bool"
            )

        self._reconnect_flapping_enabled = (
            reconnect_flapping_enabled
        )

    def process(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        snapshot: SessionSnapshot,
        transitions: tuple[SessionTransition, ...],
        timestamp: datetime,
    ) -> SessionAlarmRuntimeResult:
        """Process one multimedia-session alarm cycle."""

        self._validate_inputs(
            node_id=node_id,
            instance_id=instance_id,
            snapshot=snapshot,
            transitions=transitions,
            timestamp=timestamp,
        )

        expected_results: list[
            ExpectedSessionAlarmResult
        ] = []

        expected_evaluations = (
            self._expected_session_evaluator.evaluate(
                snapshot=snapshot,
                policies=self._expected_session_policies,
            )
        )

        for evaluation in expected_evaluations:
            stabilization = (
                self._expected_session_stabilizer.stabilize(
                    evaluation=evaluation,
                    observed_at=timestamp,
                )
            )

            result = (
                self._expected_session_alarm_service.process(
                    node_id=node_id,
                    instance_id=instance_id,
                    stabilization=stabilization,
                    timestamp=timestamp,
                )
            )

            expected_results.append(result)

        reconnect_results: list[
            ReconnectFlappingAlarmResult
        ] = []

        if self._reconnect_flapping_enabled:
            touched_identities = set()

            for transition in transitions:
                evaluation = (
                    self._reconnect_flapping_evaluator.evaluate(
                        transition=transition,
                        observed_at=timestamp,
                    )
                )

                touched_identities.add(
                    evaluation.identity
                )

                result = (
                    self._reconnect_flapping_alarm_service.process(
                        node_id=node_id,
                        instance_id=instance_id,
                        evaluation=evaluation,
                        timestamp=timestamp,
                    )
                )

                reconnect_results.append(result)

            #
            # Age reconnect histories even when no new transition occurs.
            #
            for identity in tuple(
                self._reconnect_flapping_evaluator.identities()
            ):
                if identity in touched_identities:
                    continue

                evaluation = (
                    self._reconnect_flapping_evaluator.observe(
                        identity=identity,
                        observed_at=timestamp,
                    )
                )

                result = (
                    self._reconnect_flapping_alarm_service.process(
                        node_id=node_id,
                        instance_id=instance_id,
                        evaluation=evaluation,
                        timestamp=timestamp,
                    )
                )

                reconnect_results.append(result)

        critical_results: list[
            CriticalPathNoReadersAlarmResult
        ] = []

        critical_evaluations = (
            self._critical_path_evaluator.evaluate(
                snapshot=snapshot,
                policies=self._critical_path_policies,
            )
        )

        for evaluation in critical_evaluations:
            stabilization = (
                self._critical_path_stabilizer.stabilize(
                    evaluation=evaluation,
                    observed_at=timestamp,
                )
            )

            result = (
                self._critical_path_alarm_service.process(
                    node_id=node_id,
                    instance_id=instance_id,
                    stabilization=stabilization,
                    timestamp=timestamp,
                )
            )

            critical_results.append(result)

        return SessionAlarmRuntimeResult(
            expected_session_results=tuple(
                expected_results
            ),
            reconnect_flapping_results=tuple(
                reconnect_results
            ),
            critical_path_results=tuple(
                critical_results
            ),
        )

    @staticmethod
    def _validate_inputs(
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        snapshot: SessionSnapshot,
        transitions: tuple[SessionTransition, ...],
        timestamp: datetime,
    ) -> None:
        if not isinstance(node_id, NodeId):
            raise TypeError(
                "node_id must be a NodeId"
            )

        if not isinstance(instance_id, NodeInstanceId):
            raise TypeError(
                "instance_id must be a NodeInstanceId"
            )

        if not isinstance(snapshot, SessionSnapshot):
            raise TypeError(
                "snapshot must be a SessionSnapshot"
            )

        if not isinstance(transitions, tuple):
            raise TypeError(
                "transitions must be a tuple"
            )

        for transition in transitions:
            if not isinstance(
                transition,
                SessionTransition,
            ):
                raise TypeError(
                    "transitions must contain only "
                    "SessionTransition values"
                )

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
