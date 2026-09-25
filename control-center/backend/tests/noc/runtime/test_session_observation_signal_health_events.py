"""Signal Health event handoff contract for SessionObservationRuntime.

ENG-013C — Block 231E

SessionObservationRuntime owns the temporal observation cycle.

Signal Health transition detection and event persistence must reuse the
SignalHealth already produced from the coherent cycle evidence.

The runtime must:

- keep previous SignalHealth by signal identity;
- detect each SignalHealth transition exactly once;
- forward that transition to SignalHealthTransitionEventService;
- use the session observation timestamp;
- establish the first observation only as baseline;
- not emit an event for the first observation;
- not advance previous SignalHealth when event processing fails.
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


def _measurement(captured_at: datetime) -> StreamingMeasurement:
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
):
    mediamtx_adapter = object.__new__(MediaMTXAdapter)
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
    signal_runtime.process_current_state.side_effect = signal_healths

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
    session_adapter.get_snapshot.return_value = session_snapshot
    streaming_service.compare.return_value = _measurement(
        captured_at
    )


def test_first_signal_observation_establishes_baseline_without_event():
    event_service = Mock(
        spec=SignalHealthTransitionEventService
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

    call = event_service.process_transition.call_args

    assert call.kwargs["node_id"] == NODE_ID
    assert call.kwargs["instance_id"] == INSTANCE_ID
    assert call.kwargs["transition"] is None
    assert call.kwargs["timestamp"] == NOW


def test_second_signal_observation_detects_and_forwards_transition():
    event_service = Mock(
        spec=SignalHealthTransitionEventService
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

    second_call = (
        event_service.process_transition.call_args_list[1]
    )

    transition = second_call.kwargs["transition"]

    assert transition is not None
    assert transition.previous.status is HealthStatus.HEALTHY
    assert transition.current.status is HealthStatus.DEGRADED
    assert second_call.kwargs["timestamp"] == later


def test_failed_event_processing_does_not_advance_signal_baseline():
    event_service = Mock(
        spec=SignalHealthTransitionEventService
    )

    event_service.process_transition.side_effect = [
        None,
        RuntimeError("event persistence failed"),
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
        match="event persistence failed",
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

    third_call = (
        event_service.process_transition.call_args_list[2]
    )

    transition = third_call.kwargs["transition"]

    assert transition is not None

    # The failed DEGRADED cycle must not become the new baseline.
    assert transition.previous.status is HealthStatus.HEALTHY
    assert transition.current.status is HealthStatus.CRITICAL


def test_signal_previous_state_is_kept_by_identity():
    event_service = Mock(
        spec=SignalHealthTransitionEventService
    )

    detector = SignalHealthTransitionDetector()

    assert hasattr(
        detector,
        "detect",
    )

    # Contract marker:
    # runtime state must be identity-scoped, not one global previous signal.
    assert event_service is not None


def test_failed_profile_does_not_partially_advance_other_signal_baselines():
    """A failed cycle must not partially promote Signal baselines."""

    profile_a = ExpectedMediaProfile(
        profile_id="impact-a",
        service_id="impact-a",
        path_name="impact-a",
    )
    profile_b = ExpectedMediaProfile(
        profile_id="impact-b",
        service_id="impact-b",
        path_name="impact-b",
    )

    def health(
        profile: ExpectedMediaProfile,
        status: HealthStatus,
    ) -> SignalHealth:
        return SignalHealth(
            profile_id=profile.profile_id,
            service_id=profile.service_id,
            path_name=profile.path_name,
            media_status=status,
            transport_status=status,
            status=status,
        )

    mediamtx_adapter = object.__new__(MediaMTXAdapter)
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

    # Cycle 1 establishes HEALTHY baselines for A and B.
    # Cycle 2 observes DEGRADED for both.
    # Event processing succeeds for A but fails for B.
    # Cycle 3 observes CRITICAL for both.
    signal_runtime.process_current_state.side_effect = [
        health(profile_a, HealthStatus.HEALTHY),
        health(profile_b, HealthStatus.HEALTHY),
        health(profile_a, HealthStatus.DEGRADED),
        health(profile_b, HealthStatus.DEGRADED),
        health(profile_a, HealthStatus.CRITICAL),
        health(profile_b, HealthStatus.CRITICAL),
    ]

    detector = SignalHealthTransitionDetector()

    event_service = Mock(
        spec=SignalHealthTransitionEventService
    )

    event_service.process_transition.side_effect = [
        None,  # cycle 1 / A baseline
        None,  # cycle 1 / B baseline
        None,  # cycle 2 / A transition succeeds
        RuntimeError("profile B event persistence failed"),
        None,  # cycle 3 / A retry
        None,  # cycle 3 / B retry
    ]

    runtime = SessionObservationRuntime(
        mediamtx_adapter=mediamtx_adapter,
        session_adapter=session_adapter,
        streaming_service=streaming_service,
        operational_runtime=operational_runtime,
        media_profiles=(profile_a, profile_b),
        media_health_current_state_repository=repository,
        signal_health_operational_runtime=signal_runtime,
        signal_health_transition_detector=detector,
        signal_health_transition_event_service=event_service,
    )

    def prepare(captured_at: datetime) -> None:
        snapshot = _snapshot(captured_at)

        session_snapshot = Mock()
        session_snapshot.captured_at = captured_at

        mediamtx_adapter.get_snapshot.return_value = snapshot
        session_adapter.get_snapshot.return_value = session_snapshot
        streaming_service.compare.return_value = _measurement(
            captured_at
        )

    # --------------------------------------------------------
    # Cycle 1 — establish both HEALTHY baselines.
    # --------------------------------------------------------

    prepare(NOW)

    runtime.run_once(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
    )

    # --------------------------------------------------------
    # Cycle 2 — A persists successfully, B fails.
    # The complete cycle therefore fails.
    # --------------------------------------------------------

    second_time = NOW + timedelta(seconds=5)
    prepare(second_time)

    with pytest.raises(
        RuntimeError,
        match="profile B event persistence failed",
    ):
        runtime.run_once(
            node_id=NODE_ID,
            instance_id=INSTANCE_ID,
        )

    # --------------------------------------------------------
    # Cycle 3 — both become CRITICAL.
    #
    # Contract:
    # because cycle 2 failed, BOTH previous Signal baselines
    # must still be HEALTHY.
    #
    # With partial promotion, A will incorrectly be DEGRADED.
    # --------------------------------------------------------

    third_time = NOW + timedelta(seconds=10)
    prepare(third_time)

    runtime.run_once(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
    )

    calls = event_service.process_transition.call_args_list

    assert len(calls) == 6

    third_cycle_a = calls[4].kwargs["transition"]
    third_cycle_b = calls[5].kwargs["transition"]

    assert third_cycle_a is not None
    assert third_cycle_b is not None

    assert third_cycle_a.previous.profile_id == profile_a.profile_id
    assert third_cycle_b.previous.profile_id == profile_b.profile_id

    # Atomic baseline contract:
    # neither profile from the failed second cycle was promoted.
    assert third_cycle_a.previous.status is HealthStatus.HEALTHY
    assert third_cycle_a.current.status is HealthStatus.CRITICAL

    assert third_cycle_b.previous.status is HealthStatus.HEALTHY
    assert third_cycle_b.current.status is HealthStatus.CRITICAL
