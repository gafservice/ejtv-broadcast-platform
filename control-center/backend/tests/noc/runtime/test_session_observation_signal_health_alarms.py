"""Signal Health alarm handoff contract for SessionObservationRuntime.

ENG-013C — Block 232E.2

SessionObservationRuntime already owns the coherent Signal Health transition
boundary.

The alarm integration must:

- reuse the exact SignalHealthTransition already sent to Events;
- use the exact session observation timestamp;
- process the first observation as transition=None;
- invoke Events before Alarms;
- not advance the Signal Health baseline when alarm processing fails.

It must not:

- recalculate Signal Health;
- redetect the transition;
- create another observation cycle;
- persist alarms directly.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import pytest

from app.adapters.mediamtx.adapter import MediaMTXAdapter
from app.adapters.mediamtx.session_adapter import MediaMTXSessionAdapter
from app.domain.streaming.expected_media_profile import ExpectedMediaProfile
from app.domain.streaming.health import HealthStatus
from app.domain.streaming.metrics import (
    MeasurementQuality,
    StreamingMeasurement,
    StreamingPathMeasurement,
)
from app.domain.streaming.models import (
    MediaMTXSnapshot,
    MediaPath,
    MediaPathStatus,
    MediaSource,
)
from app.domain.streaming.signal_health import SignalHealth
from app.noc.current_state.media_health_current_state import (
    MediaHealthCurrentStateRepository,
)
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.runtime.session_observation_runtime import (
    SessionObservationRuntime,
)
from app.noc.runtime.session_operational_runtime import (
    SessionOperationalRuntime,
)
from app.noc.runtime.signal_health_operational_runtime import (
    SignalHealthOperationalRuntime,
)
from app.services.signal_health_transition_alarm_service import (
    SignalHealthTransitionAlarmService,
)
from app.services.signal_health_transition_detector import (
    SignalHealthTransitionDetector,
)
from app.services.signal_health_transition_event_service import (
    SignalHealthTransitionEventService,
)
from app.services.streaming_service import StreamingService


NODE_ID = NodeId.create(
    id="streaming-core",
    name="streaming",
    display_name="Streaming Core",
)

INSTANCE_ID = NodeInstanceId("streaming-primary")

NOW = datetime(
    2026,
    9,
    25,
    6,
    0,
    tzinfo=timezone.utc,
)


def _profile() -> ExpectedMediaProfile:
    return ExpectedMediaProfile(
        profile_id="impact-main",
        service_id="impact",
        path_name="impact",
    )


def _snapshot(captured_at: datetime) -> MediaMTXSnapshot:
    return MediaMTXSnapshot(
        captured_at=captured_at,
        paths=(
            MediaPath(
                name="impact",
                configuration_name="impact",
                status=MediaPathStatus.ACTIVE,
                ready=True,
                available=True,
                online=True,
                source=MediaSource(
                    source_type="srtSource",
                ),
                inbound_bytes=1_000_000,
            ),
        ),
        reported_item_count=1,
        reported_page_count=1,
    )


def _measurement(
    captured_at: datetime,
) -> StreamingMeasurement:
    path = StreamingPathMeasurement(
        name="impact",
        status=MediaPathStatus.ACTIVE,
        previous_status=MediaPathStatus.ACTIVE,
        reader_count=0,
        reader_delta=0,
        inbound_delta_bytes=500_000,
        outbound_delta_bytes=0,
        inbound_bitrate_bps=800_000.0,
        outbound_bitrate_bps=0.0,
        state_changed=False,
        quality=MeasurementQuality.AVAILABLE,
    )

    return StreamingMeasurement(
        captured_at=captured_at,
        previous_captured_at=captured_at,
        interval_seconds=5.0,
        paths=(path,),
        total_inbound_bitrate_bps=800_000.0,
        total_outbound_bitrate_bps=0.0,
        quality=MeasurementQuality.AVAILABLE,
    )


def _health(status: HealthStatus) -> SignalHealth:
    return SignalHealth(
        profile_id="impact-main",
        service_id="impact",
        path_name="impact",
        media_status=status,
        transport_status=status,
        status=status,
    )


def _build_runtime(
    *,
    signal_healths: list[SignalHealth],
    event_service,
    alarm_service,
):
    mediamtx_adapter = object.__new__(
        MediaMTXAdapter
    )
    mediamtx_adapter.get_snapshot = Mock()

    session_adapter = object.__new__(
        MediaMTXSessionAdapter
    )
    session_adapter.get_snapshot = Mock()

    streaming_service = Mock(
        spec=StreamingService
    )

    operational_runtime = object.__new__(
        SessionOperationalRuntime
    )
    operational_runtime.process = Mock(
        return_value=Mock()
    )

    repository = Mock(
        spec=MediaHealthCurrentStateRepository
    )
    repository.latest.return_value = None

    signal_runtime = Mock(
        spec=SignalHealthOperationalRuntime
    )
    signal_runtime.process_current_state.side_effect = (
        signal_healths
    )

    detector = SignalHealthTransitionDetector()

    runtime = SessionObservationRuntime(
        mediamtx_adapter=mediamtx_adapter,
        session_adapter=session_adapter,
        streaming_service=streaming_service,
        operational_runtime=operational_runtime,
        media_profiles=(_profile(),),
        media_health_current_state_repository=repository,
        signal_health_operational_runtime=signal_runtime,
        signal_health_transition_detector=detector,
        signal_health_transition_event_service=event_service,
        signal_health_transition_alarm_service=alarm_service,
    )

    return (
        runtime,
        mediamtx_adapter,
        session_adapter,
        streaming_service,
    )


def _prepare_cycle(
    *,
    mediamtx_adapter,
    session_adapter,
    streaming_service,
    captured_at: datetime,
) -> None:
    snapshot = _snapshot(captured_at)

    session_snapshot = Mock()
    session_snapshot.captured_at = captured_at

    mediamtx_adapter.get_snapshot.return_value = snapshot
    session_adapter.get_snapshot.return_value = (
        session_snapshot
    )
    streaming_service.compare.return_value = (
        _measurement(captured_at)
    )


def test_first_observation_is_forwarded_to_events_and_alarms():
    event_service = Mock(
        spec=SignalHealthTransitionEventService
    )
    alarm_service = Mock(
        spec=SignalHealthTransitionAlarmService
    )

    (
        runtime,
        mediamtx_adapter,
        session_adapter,
        streaming_service,
    ) = _build_runtime(
        signal_healths=[
            _health(HealthStatus.HEALTHY),
        ],
        event_service=event_service,
        alarm_service=alarm_service,
    )

    _prepare_cycle(
        mediamtx_adapter=mediamtx_adapter,
        session_adapter=session_adapter,
        streaming_service=streaming_service,
        captured_at=NOW,
    )

    runtime.run_once(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
    )

    event_service.process_transition.assert_called_once()
    alarm_service.process_transition.assert_called_once()

    event_call = event_service.process_transition.call_args
    alarm_call = alarm_service.process_transition.call_args

    assert event_call.kwargs["transition"] is None
    assert alarm_call.kwargs["transition"] is None

    assert event_call.kwargs["timestamp"] == NOW
    assert alarm_call.kwargs["timestamp"] == NOW

    assert event_call.kwargs["node_id"] == NODE_ID
    assert alarm_call.kwargs["node_id"] == NODE_ID

    assert event_call.kwargs["instance_id"] == INSTANCE_ID
    assert alarm_call.kwargs["instance_id"] == INSTANCE_ID


def test_events_and_alarms_receive_exact_same_transition_object():
    event_service = Mock(
        spec=SignalHealthTransitionEventService
    )
    alarm_service = Mock(
        spec=SignalHealthTransitionAlarmService
    )

    (
        runtime,
        mediamtx_adapter,
        session_adapter,
        streaming_service,
    ) = _build_runtime(
        signal_healths=[
            _health(HealthStatus.HEALTHY),
            _health(HealthStatus.DEGRADED),
        ],
        event_service=event_service,
        alarm_service=alarm_service,
    )

    _prepare_cycle(
        mediamtx_adapter=mediamtx_adapter,
        session_adapter=session_adapter,
        streaming_service=streaming_service,
        captured_at=NOW,
    )

    runtime.run_once(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
    )

    later = NOW + timedelta(seconds=5)

    _prepare_cycle(
        mediamtx_adapter=mediamtx_adapter,
        session_adapter=session_adapter,
        streaming_service=streaming_service,
        captured_at=later,
    )

    runtime.run_once(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
    )

    assert event_service.process_transition.call_count == 2
    assert alarm_service.process_transition.call_count == 2

    event_call = (
        event_service.process_transition.call_args_list[1]
    )
    alarm_call = (
        alarm_service.process_transition.call_args_list[1]
    )

    event_transition = event_call.kwargs["transition"]
    alarm_transition = alarm_call.kwargs["transition"]

    assert event_transition is not None
    assert alarm_transition is event_transition

    assert (
        event_transition.previous.status
        is HealthStatus.HEALTHY
    )
    assert (
        event_transition.current.status
        is HealthStatus.DEGRADED
    )

    assert event_call.kwargs["timestamp"] == later
    assert alarm_call.kwargs["timestamp"] == later


def test_failed_alarm_processing_does_not_advance_signal_baseline():
    event_service = Mock(
        spec=SignalHealthTransitionEventService
    )

    alarm_service = Mock(
        spec=SignalHealthTransitionAlarmService
    )
    alarm_service.process_transition.side_effect = [
        None,
        RuntimeError("signal alarm processing failed"),
        None,
    ]

    (
        runtime,
        mediamtx_adapter,
        session_adapter,
        streaming_service,
    ) = _build_runtime(
        signal_healths=[
            _health(HealthStatus.HEALTHY),
            _health(HealthStatus.DEGRADED),
            _health(HealthStatus.CRITICAL),
        ],
        event_service=event_service,
        alarm_service=alarm_service,
    )

    _prepare_cycle(
        mediamtx_adapter=mediamtx_adapter,
        session_adapter=session_adapter,
        streaming_service=streaming_service,
        captured_at=NOW,
    )

    runtime.run_once(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
    )

    second_time = NOW + timedelta(seconds=5)

    _prepare_cycle(
        mediamtx_adapter=mediamtx_adapter,
        session_adapter=session_adapter,
        streaming_service=streaming_service,
        captured_at=second_time,
    )

    with pytest.raises(
        RuntimeError,
        match="signal alarm processing failed",
    ):
        runtime.run_once(
            node_id=NODE_ID,
            instance_id=INSTANCE_ID,
        )

    third_time = NOW + timedelta(seconds=10)

    _prepare_cycle(
        mediamtx_adapter=mediamtx_adapter,
        session_adapter=session_adapter,
        streaming_service=streaming_service,
        captured_at=third_time,
    )

    runtime.run_once(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
    )

    assert alarm_service.process_transition.call_count == 3

    third_call = (
        alarm_service.process_transition.call_args_list[2]
    )

    value = third_call.kwargs["transition"]

    assert value is not None

    # Failed DEGRADED alarm cycle must not become baseline.
    assert value.previous.status is HealthStatus.HEALTHY
    assert value.current.status is HealthStatus.CRITICAL


def test_alarm_dependency_is_exposed_by_runtime():
    event_service = Mock(
        spec=SignalHealthTransitionEventService
    )
    alarm_service = Mock(
        spec=SignalHealthTransitionAlarmService
    )

    (
        runtime,
        _,
        _,
        _,
    ) = _build_runtime(
        signal_healths=[
            _health(HealthStatus.HEALTHY),
        ],
        event_service=event_service,
        alarm_service=alarm_service,
    )

    assert (
        runtime._signal_health_transition_alarm_service
        is alarm_service
    )
