"""Productive Signal Health handoff contract.

ENG-013C — Block 220

The existing SessionObservationRuntime owns the coherent MediaMTX
snapshot and StreamingMeasurement for one temporal cycle.

Signal Health productive integration must reuse that evidence and read
the latest stabilized Media Health current state. It must not capture
MediaMTX again, derive a second measurement, own another clock, or
create another background loop.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import Mock

from app.domain.streaming.expected_media_profile import (
    ExpectedMediaProfile,
)
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
from app.noc.runtime.session_observation_runtime import (
    SessionObservationRuntime,
)
from app.noc.runtime.signal_health_operational_runtime import (
    SignalHealthOperationalRuntime,
)
from app.services.streaming_service import StreamingService
from app.adapters.mediamtx.adapter import MediaMTXAdapter
from app.adapters.mediamtx.session_adapter import MediaMTXSessionAdapter
from app.noc.runtime.session_operational_runtime import SessionOperationalRuntime
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId


NODE_ID = NodeId.create(
    id="streaming-core",
    name="streaming",
    display_name="Streaming Core",
)

INSTANCE_ID = NodeInstanceId("streaming-primary")


NOW = datetime(
    2026,
    9,
    24,
    14,
    30,
    tzinfo=timezone.utc,
)


def _profile() -> ExpectedMediaProfile:
    return ExpectedMediaProfile(
        profile_id="impact-main",
        service_id="impact",
        path_name="impact",
    )


def _media_snapshot() -> MediaMTXSnapshot:
    return MediaMTXSnapshot(
        captured_at=NOW,
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


def _measurement() -> StreamingMeasurement:
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
        captured_at=NOW,
        previous_captured_at=NOW,
        interval_seconds=5.0,
        paths=(path,),
        total_inbound_bitrate_bps=800_000.0,
        total_outbound_bitrate_bps=0.0,
        quality=MeasurementQuality.AVAILABLE,
    )


def _signal_health() -> SignalHealth:
    return SignalHealth(
        profile_id="impact-main",
        service_id="impact",
        path_name="impact",
        media_status=HealthStatus.HEALTHY,
        transport_status=HealthStatus.HEALTHY,
        status=HealthStatus.HEALTHY,
    )


def _build_runtime(
    *,
    repository,
    signal_runtime,
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

    media_snapshot = _media_snapshot()
    measurement = _measurement()

    mediamtx_adapter.get_snapshot.return_value = media_snapshot
    session_adapter.get_snapshot.return_value = Mock()

    streaming_service.compare.return_value = measurement

    runtime = SessionObservationRuntime(
        mediamtx_adapter=mediamtx_adapter,
        session_adapter=session_adapter,
        streaming_service=streaming_service,
        operational_runtime=operational_runtime,
        media_profiles=(_profile(),),
        media_health_current_state_repository=repository,
        signal_health_operational_runtime=signal_runtime,
    )

    return (
        runtime,
        mediamtx_adapter,
        session_adapter,
        streaming_service,
        operational_runtime,
        media_snapshot,
        measurement,
    )


def test_session_cycle_reads_media_current_state_by_profile_identity():
    repository = Mock(
        spec=MediaHealthCurrentStateRepository
    )
    repository.latest.return_value = None

    signal_runtime = Mock(
        spec=SignalHealthOperationalRuntime
    )
    signal_runtime.process_current_state.return_value = (
        _signal_health()
    )

    runtime, *_ = _build_runtime(
        repository=repository,
        signal_runtime=signal_runtime,
    )

    runtime.run_once(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
    )

    repository.latest.assert_called_once_with(
        profile_id="impact-main",
        service_id="impact",
        path_name="impact",
    )


def test_session_cycle_reuses_same_snapshot_and_measurement_for_signal_health():
    repository = Mock(
        spec=MediaHealthCurrentStateRepository
    )
    repository.latest.return_value = None

    signal_runtime = Mock(
        spec=SignalHealthOperationalRuntime
    )
    signal_runtime.process_current_state.return_value = (
        _signal_health()
    )

    (
        runtime,
        _,
        _,
        _,
        _,
        media_snapshot,
        measurement,
    ) = _build_runtime(
        repository=repository,
        signal_runtime=signal_runtime,
    )

    runtime.run_once(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
    )

    signal_runtime.process_current_state.assert_called_once()

    call = (
        signal_runtime
        .process_current_state
        .call_args
    )

    assert call.kwargs["profile"] == _profile()
    assert call.kwargs["media_current_state"] is None

    assert (
        call.kwargs["media_snapshot"]
        is media_snapshot
    )

    assert (
        call.kwargs["measurement"]
        is measurement
    )


def test_missing_media_current_state_is_forwarded_without_synthetic_health():
    repository = Mock(
        spec=MediaHealthCurrentStateRepository
    )
    repository.latest.return_value = None

    signal_runtime = Mock(
        spec=SignalHealthOperationalRuntime
    )
    signal_runtime.process_current_state.return_value = (
        _signal_health()
    )

    runtime, *_ = _build_runtime(
        repository=repository,
        signal_runtime=signal_runtime,
    )

    runtime.run_once(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
    )

    call = (
        signal_runtime
        .process_current_state
        .call_args
    )

    assert (
        call.kwargs["media_current_state"]
        is None
    )


def test_signal_handoff_does_not_trigger_second_mediamtx_capture():
    repository = Mock(
        spec=MediaHealthCurrentStateRepository
    )
    repository.latest.return_value = None

    signal_runtime = Mock(
        spec=SignalHealthOperationalRuntime
    )
    signal_runtime.process_current_state.return_value = (
        _signal_health()
    )

    (
        runtime,
        mediamtx_adapter,
        _,
        _,
        _,
        _,
        _,
    ) = _build_runtime(
        repository=repository,
        signal_runtime=signal_runtime,
    )

    runtime.run_once(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
    )

    mediamtx_adapter.get_snapshot.assert_called_once()


def test_signal_handoff_does_not_recalculate_streaming_measurement():
    repository = Mock(
        spec=MediaHealthCurrentStateRepository
    )
    repository.latest.return_value = None

    signal_runtime = Mock(
        spec=SignalHealthOperationalRuntime
    )
    signal_runtime.process_current_state.return_value = (
        _signal_health()
    )

    (
        runtime,
        _,
        _,
        streaming_service,
        _,
        _,
        _,
    ) = _build_runtime(
        repository=repository,
        signal_runtime=signal_runtime,
    )

    runtime.run_once(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
    )

    streaming_service.compare.assert_called_once()

def test_future_media_current_state_is_not_handed_to_signal_health() -> None:
    """A session snapshot must not consume Media Health from its future."""

    from datetime import timedelta

    from app.domain.streaming.media_health import MediaHealth
    from app.noc.current_state.media_health_current_state import (
        MediaHealthCurrentState,
    )

    repository = Mock(
        spec=MediaHealthCurrentStateRepository
    )

    future_state = MediaHealthCurrentState(
        profile_id="impact-main",
        service_id="impact",
        path_name="impact",
        observed_at=NOW + timedelta(microseconds=1),
        health=MediaHealth(
            profile_id="impact-main",
            service_id="impact",
            path_name="impact",
            status=HealthStatus.HEALTHY,
        ),
    )

    repository.latest.return_value = future_state

    signal_runtime = Mock(
        spec=SignalHealthOperationalRuntime
    )
    signal_runtime.process_current_state.return_value = (
        _signal_health()
    )

    (
        runtime,
        _,
        _,
        _,
        _,
        media_snapshot,
        measurement,
    ) = _build_runtime(
        repository=repository,
        signal_runtime=signal_runtime,
    )

    runtime.run_once(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
    )

    repository.latest.assert_called_once_with(
        profile_id="impact-main",
        service_id="impact",
        path_name="impact",
    )

    signal_runtime.process_current_state.assert_called_once()

    call = signal_runtime.process_current_state.call_args

    assert call.kwargs["profile"] == _profile()

    assert call.kwargs["media_current_state"] is None

    assert (
        call.kwargs["media_snapshot"]
        is media_snapshot
    )

    assert (
        call.kwargs["measurement"]
        is measurement
    )


def test_equal_timestamp_media_current_state_is_handed_to_signal_health() -> None:
    """Media Health observed exactly at snapshot time belongs to that cycle."""

    from app.domain.streaming.media_health import MediaHealth
    from app.noc.current_state.media_health_current_state import (
        MediaHealthCurrentState,
    )

    repository = Mock(
        spec=MediaHealthCurrentStateRepository
    )

    current_state = MediaHealthCurrentState(
        profile_id="impact-main",
        service_id="impact",
        path_name="impact",
        observed_at=NOW,
        health=MediaHealth(
            profile_id="impact-main",
            service_id="impact",
            path_name="impact",
            status=HealthStatus.HEALTHY,
        ),
    )

    repository.latest.return_value = current_state

    signal_runtime = Mock(
        spec=SignalHealthOperationalRuntime
    )
    signal_runtime.process_current_state.return_value = (
        _signal_health()
    )

    (
        runtime,
        _,
        _,
        _,
        _,
        media_snapshot,
        measurement,
    ) = _build_runtime(
        repository=repository,
        signal_runtime=signal_runtime,
    )

    runtime.run_once(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
    )

    signal_runtime.process_current_state.assert_called_once()

    call = signal_runtime.process_current_state.call_args

    assert (
        call.kwargs["media_current_state"]
        is current_state
    )

    assert (
        call.kwargs["media_snapshot"]
        is media_snapshot
    )

    assert (
        call.kwargs["measurement"]
        is measurement
    )
