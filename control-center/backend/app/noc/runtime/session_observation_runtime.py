"""Periodic observation runtime for multimedia sessions.

ENG-013B — Node SDK

SessionObservationRuntime owns the temporal observation state required
to feed SessionOperationalRuntime.

It captures MediaMTX and session snapshots, derives streaming
measurements from consecutive media snapshots, and delegates all
session transition/event/alarm decisions to SessionOperationalRuntime.

It does not render dashboards and does not own persistence.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from app.adapters.mediamtx.adapter import MediaMTXAdapter
from app.adapters.mediamtx.session_adapter import MediaMTXSessionAdapter
from app.domain.sessions import SessionSnapshot
from app.domain.streaming import MediaMTXSnapshot
from app.domain.streaming.metrics import StreamingMeasurement
from app.domain.streaming.signal_health import SignalHealth
from app.domain.streaming.expected_media_profile import ExpectedMediaProfile
from app.noc.current_state.media_health_current_state import (
    MediaHealthCurrentStateRepository,
)
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.runtime.session_operational_runtime import (
    SessionOperationalRuntime,
    SessionOperationalRuntimeResult,
)
from app.noc.runtime.signal_health_operational_runtime import (
    SignalHealthOperationalRuntime,
)
from app.services.signal_health_transition_detector import (
    SignalHealthTransitionDetector,
)
from app.services.signal_health_transition_event_service import (
    SignalHealthTransitionEventService,
)
from app.services.signal_health_transition_alarm_service import (
    SignalHealthTransitionAlarmService,
)
from app.services.streaming_service import StreamingService


@dataclass(frozen=True, slots=True)
class SessionObservationResult:
    """Result of one multimedia observation cycle."""

    media_snapshot: MediaMTXSnapshot
    session_snapshot: SessionSnapshot
    streaming_measurement: StreamingMeasurement
    operational_result: SessionOperationalRuntimeResult


class SessionObservationRuntime:
    """Capture multimedia state and feed the operational session runtime."""

    def __init__(
        self,
        *,
        mediamtx_adapter: MediaMTXAdapter,
        session_adapter: MediaMTXSessionAdapter,
        streaming_service: StreamingService,
        operational_runtime: SessionOperationalRuntime,
        media_profiles: tuple[ExpectedMediaProfile, ...] = (),
        media_health_current_state_repository: (
            MediaHealthCurrentStateRepository | None
        ) = None,
        signal_health_operational_runtime: (
            SignalHealthOperationalRuntime | None
        ) = None,
        signal_health_transition_detector: (
            SignalHealthTransitionDetector | None
        ) = None,
        signal_health_transition_event_service: (
            SignalHealthTransitionEventService | None
        ) = None,
        signal_health_transition_alarm_service: (
            SignalHealthTransitionAlarmService | None
        ) = None,
    ) -> None:
        if not isinstance(mediamtx_adapter, MediaMTXAdapter):
            raise TypeError(
                "mediamtx_adapter must be a MediaMTXAdapter"
            )

        if not isinstance(
            session_adapter,
            MediaMTXSessionAdapter,
        ):
            raise TypeError(
                "session_adapter must be a MediaMTXSessionAdapter"
            )

        if not isinstance(streaming_service, StreamingService):
            raise TypeError(
                "streaming_service must be a StreamingService"
            )

        if not isinstance(
            operational_runtime,
            SessionOperationalRuntime,
        ):
            raise TypeError(
                "operational_runtime must be a "
                "SessionOperationalRuntime"
            )

        signal_dependencies = (
            media_health_current_state_repository,
            signal_health_operational_runtime,
        )

        if media_profiles and any(
            dependency is None
            for dependency in signal_dependencies
        ):
            raise ValueError(
                "media_profiles require both "
                "media_health_current_state_repository and "
                "signal_health_operational_runtime"
            )

        if not media_profiles and any(
            dependency is not None
            for dependency in signal_dependencies
        ):
            raise ValueError(
                "Signal Health dependencies require media_profiles"
            )

        signal_event_dependencies = (
            signal_health_transition_detector,
            signal_health_transition_event_service,
        )

        if any(
            dependency is None
            for dependency in signal_event_dependencies
        ) and any(
            dependency is not None
            for dependency in signal_event_dependencies
        ):
            raise ValueError(
                "Signal Health transition detector and event service "
                "must be configured together"
            )

        if not media_profiles and any(
            dependency is not None
            for dependency in signal_event_dependencies
        ):
            raise ValueError(
                "Signal Health event dependencies require media_profiles"
            )

        self._mediamtx_adapter = mediamtx_adapter
        self._session_adapter = session_adapter
        self._streaming_service = streaming_service
        self._operational_runtime = operational_runtime

        self._media_profiles = tuple(media_profiles)
        self._media_health_current_state_repository = (
            media_health_current_state_repository
        )
        self._signal_health_operational_runtime = (
            signal_health_operational_runtime
        )
        self._signal_health_transition_detector = (
            signal_health_transition_detector
        )
        self._signal_health_transition_event_service = (
            signal_health_transition_event_service
        )
        self._signal_health_transition_alarm_service = (
            signal_health_transition_alarm_service
        )

        self._previous_media_snapshot: MediaMTXSnapshot | None = None
        self._previous_session_snapshot: SessionSnapshot | None = None
        self._previous_signal_health_by_identity: dict[
            tuple[str, str, str | None], SignalHealth
        ] = {}

    def run_once(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
    ) -> SessionObservationResult:
        """Execute one operational multimedia observation cycle."""

        media_snapshot = self._mediamtx_adapter.get_snapshot()
        session_snapshot = self._session_adapter.get_snapshot()

        streaming_measurement = self._streaming_service.compare(
            self._previous_media_snapshot,
            media_snapshot,
        )

        operational_result = self._operational_runtime.process(
            node_id=node_id,
            instance_id=instance_id,
            previous=self._previous_session_snapshot,
            current=session_snapshot,
            media_snapshot=media_snapshot,
            streaming_measurement=streaming_measurement,
            timestamp=session_snapshot.captured_at,
        )

        if self._media_profiles:
            repository = (
                self._media_health_current_state_repository
            )
            signal_runtime = (
                self._signal_health_operational_runtime
            )

            assert repository is not None
            assert signal_runtime is not None

            pending_signal_health_by_identity: dict[
                tuple[str, str, str | None], SignalHealth
            ] = {}

            for profile in self._media_profiles:
                media_current_state = repository.latest(
                    profile_id=profile.profile_id,
                    service_id=profile.service_id,
                    path_name=profile.path_name,
                )

                if (
                    media_current_state is not None
                    and media_current_state.observed_at
                    > media_snapshot.captured_at
                ):
                    media_current_state = None

                current_signal_health = (
                    signal_runtime.process_current_state(
                        profile=profile,
                        media_current_state=media_current_state,
                        media_snapshot=media_snapshot,
                        measurement=streaming_measurement,
                    )
                )

                detector = (
                    self._signal_health_transition_detector
                )
                event_service = (
                    self._signal_health_transition_event_service
                )
                alarm_service = (
                    self._signal_health_transition_alarm_service
                )

                if detector is not None and event_service is not None:
                    identity = (
                        current_signal_health.profile_id,
                        current_signal_health.service_id,
                        current_signal_health.path_name,
                    )

                    previous_signal_health = (
                        self._previous_signal_health_by_identity.get(
                            identity
                        )
                    )

                    transition = detector.detect(
                        previous_signal_health,
                        current_signal_health,
                    )

                    event_service.process_transition(
                        node_id=node_id,
                        instance_id=instance_id,
                        transition=transition,
                        timestamp=session_snapshot.captured_at,
                    )

                    if alarm_service is not None:
                        alarm_service.process_transition(
                            node_id=node_id,
                            instance_id=instance_id,
                            transition=transition,
                            timestamp=session_snapshot.captured_at,
                        )

                    pending_signal_health_by_identity[
                        identity
                    ] = current_signal_health

            self._previous_signal_health_by_identity.update(
                pending_signal_health_by_identity
            )

        self._previous_media_snapshot = media_snapshot
        self._previous_session_snapshot = session_snapshot

        return SessionObservationResult(
            media_snapshot=media_snapshot,
            session_snapshot=session_snapshot,
            streaming_measurement=streaming_measurement,
            operational_result=operational_result,
        )

    async def run_forever(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        interval_seconds: float = 5.0,
    ) -> None:
        """Continuously execute multimedia observation cycles."""

        if interval_seconds <= 0:
            raise ValueError(
                "interval_seconds must be greater than zero"
            )

        while True:
            self.run_once(
                node_id=node_id,
                instance_id=instance_id,
            )

            await asyncio.sleep(interval_seconds)
