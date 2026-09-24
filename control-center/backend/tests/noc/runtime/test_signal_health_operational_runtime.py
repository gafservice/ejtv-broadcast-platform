"""Tests for Signal Health operational composition.

ENG-013C — Signal Health

This runtime composes already-evaluated conclusions:

- stabilized MediaHealth;
- SourceTransportHealth derived from an existing StreamingMeasurement.

It must not observe media, capture MediaMTX, calculate transport metrics,
or reinterpret lower-level evidence.
"""

from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from app.domain.streaming.expected_media_profile import ExpectedMediaProfile
from app.domain.streaming.health import HealthStatus
from app.domain.streaming.media_health import MediaHealth
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
from app.domain.streaming.signal_health import (
    SignalHealth,
    SignalHealthEvaluator,
)
from app.domain.streaming.source_transport_health import SourceTransportHealth
from app.noc.runtime.signal_health_operational_runtime import (
    SignalHealthOperationalRuntime,
)
from app.services.source_transport_health_evaluator import (
    SourceTransportHealthEvaluator,
)


OBSERVED_AT = datetime(
    2026,
    9,
    23,
    22,
    30,
    tzinfo=timezone.utc,
)


def _profile() -> ExpectedMediaProfile:
    return ExpectedMediaProfile(
        profile_id="impact-main",
        service_id="impact",
        path_name="impact",
    )


def _media_health(
    status: HealthStatus = HealthStatus.HEALTHY,
) -> MediaHealth:
    return MediaHealth(
        profile_id="impact-main",
        service_id="impact",
        path_name="impact",
        status=status,
    )


def _media_snapshot(
    *,
    captured_at: datetime = OBSERVED_AT,
    source_type: str = "srtSource",
) -> MediaMTXSnapshot:
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
                    source_type=source_type,
                ),
                inbound_bytes=1_000_000,
            ),
        ),
        reported_item_count=1,
        reported_page_count=1,
    )


def _measurement() -> StreamingMeasurement:
    path_measurement = StreamingPathMeasurement(
        name="impact",
        status=MediaPathStatus.ACTIVE,
        previous_status=MediaPathStatus.ACTIVE,
        reader_count=0,
        reader_delta=0,
        inbound_delta_bytes=1_000_000,
        outbound_delta_bytes=0,
        inbound_bitrate_bps=1_600_000.0,
        outbound_bitrate_bps=0.0,
        state_changed=False,
        quality=MeasurementQuality.AVAILABLE,
    )

    return StreamingMeasurement(
        captured_at=OBSERVED_AT,
        previous_captured_at=OBSERVED_AT,
        interval_seconds=5.0,
        paths=(path_measurement,),
        total_inbound_bitrate_bps=1_600_000.0,
        total_outbound_bitrate_bps=0.0,
        quality=MeasurementQuality.AVAILABLE,
    )


def _source_health(
    status: HealthStatus = HealthStatus.HEALTHY,
) -> SourceTransportHealth:
    return SourceTransportHealth(
        service_id="impact",
        path_name="impact",
        source_type="srtSource",
        status=status,
    )


def _signal_health(
    status: HealthStatus = HealthStatus.HEALTHY,
) -> SignalHealth:
    return SignalHealth(
        profile_id="impact-main",
        service_id="impact",
        path_name="impact",
        media_status=HealthStatus.HEALTHY,
        transport_status=HealthStatus.HEALTHY,
        status=status,
    )


def test_process_combines_existing_conclusions_without_reobserving() -> None:
    source_evaluator = Mock()
    signal_evaluator = Mock()

    source_health = _source_health()
    signal_health = _signal_health()

    source_evaluator.evaluate.return_value = source_health
    signal_evaluator.evaluate.return_value = signal_health

    runtime = SignalHealthOperationalRuntime(
        source_transport_health_evaluator=source_evaluator,
        signal_health_evaluator=signal_evaluator,
    )

    profile = _profile()
    media_health = _media_health()
    measurement = _measurement()

    result = runtime.process(
        profile=profile,
        media_health=media_health,
        media_snapshot=_media_snapshot(),
        measurement=measurement,
    )

    assert result is signal_health

    source_evaluator.evaluate.assert_called_once_with(
        service_id="impact",
        source_type="srtSource",
        measurement=measurement.paths[0],
    )

    signal_evaluator.evaluate.assert_called_once_with(
        media_health=media_health,
        transport_health=source_health,
    )


def test_process_returns_unknown_source_conclusion_to_signal_evaluator() -> None:
    source_evaluator = Mock()
    signal_evaluator = Mock()

    source_health = _source_health(HealthStatus.UNKNOWN)

    expected = SignalHealth(
        profile_id="impact-main",
        service_id="impact",
        path_name="impact",
        media_status=HealthStatus.HEALTHY,
        transport_status=HealthStatus.UNKNOWN,
        status=HealthStatus.UNKNOWN,
    )

    source_evaluator.evaluate.return_value = source_health
    signal_evaluator.evaluate.return_value = expected

    runtime = SignalHealthOperationalRuntime(
        source_transport_health_evaluator=source_evaluator,
        signal_health_evaluator=signal_evaluator,
    )

    result = runtime.process(
        profile=_profile(),
        media_health=_media_health(),
        media_snapshot=_media_snapshot(),
        measurement=_measurement(),
    )

    assert result is expected


def test_process_propagates_source_evaluation_failure() -> None:
    source_evaluator = Mock()
    signal_evaluator = Mock()

    source_evaluator.evaluate.side_effect = ValueError(
        "source transport evaluation failed"
    )

    runtime = SignalHealthOperationalRuntime(
        source_transport_health_evaluator=source_evaluator,
        signal_health_evaluator=signal_evaluator,
    )

    with pytest.raises(
        ValueError,
        match="source transport evaluation failed",
    ):
        runtime.process(
            profile=_profile(),
            media_health=_media_health(),
            media_snapshot=_media_snapshot(),
            measurement=_measurement(),
        )

    signal_evaluator.evaluate.assert_not_called()


def test_process_propagates_signal_evaluation_failure() -> None:
    source_evaluator = Mock()
    signal_evaluator = Mock()

    source_evaluator.evaluate.return_value = _source_health()

    signal_evaluator.evaluate.side_effect = ValueError(
        "signal evaluation failed"
    )

    runtime = SignalHealthOperationalRuntime(
        source_transport_health_evaluator=source_evaluator,
        signal_health_evaluator=signal_evaluator,
    )

    with pytest.raises(
        ValueError,
        match="signal evaluation failed",
    ):
        runtime.process(
            profile=_profile(),
            media_health=_media_health(),
            media_snapshot=_media_snapshot(),
            measurement=_measurement(),
        )


def test_runtime_does_not_own_capture_or_observation_methods() -> None:
    assert not hasattr(
        SignalHealthOperationalRuntime,
        "run_forever",
    )
    assert not hasattr(
        SignalHealthOperationalRuntime,
        "observe",
    )
    assert not hasattr(
        SignalHealthOperationalRuntime,
        "get_snapshot",
    )


def test_process_requires_snapshot_and_measurement_same_capture_time() -> None:
    """Snapshot and measurement must describe the same capture instant."""

    import inspect

    signature = inspect.signature(
        SignalHealthOperationalRuntime.process
    )

    assert "media_snapshot" in signature.parameters
    assert "measurement" in signature.parameters
    assert "source_type" not in signature.parameters


def test_process_projects_source_type_from_media_snapshot() -> None:
    """Source identity must come from MediaMTX evidence, not caller text."""

    import inspect

    source = inspect.getsource(
        SignalHealthOperationalRuntime.process
    )

    assert "media_snapshot" in source
    assert "get_path" in source
    assert "source_type" in source


def test_process_contract_does_not_accept_external_source_type() -> None:
    """Caller must not inject source type independently of the snapshot."""

    import inspect

    signature = inspect.signature(
        SignalHealthOperationalRuntime.process
    )

    assert "source_type" not in signature.parameters


def test_process_rejects_snapshot_from_different_capture_time() -> None:
    """Transport evidence from different capture instants must not mix."""

    source_evaluator = Mock()
    signal_evaluator = Mock()

    runtime = SignalHealthOperationalRuntime(
        source_transport_health_evaluator=source_evaluator,
        signal_health_evaluator=signal_evaluator,
    )

    different_time = datetime(
        2026,
        9,
        23,
        22,
        31,
        tzinfo=timezone.utc,
    )

    with pytest.raises(
        ValueError,
        match="same capture instant",
    ):
        runtime.process(
            profile=_profile(),
            media_health=_media_health(),
            media_snapshot=_media_snapshot(
                captured_at=different_time,
            ),
            measurement=_measurement(),
        )

    source_evaluator.evaluate.assert_not_called()
    signal_evaluator.evaluate.assert_not_called()


def test_process_uses_source_type_from_matching_snapshot_path() -> None:
    """Source type must be projected from the current path evidence."""

    source_evaluator = Mock()
    signal_evaluator = Mock()

    source_health = SourceTransportHealth(
        service_id="impact",
        path_name="impact",
        source_type="futureSource",
        status=HealthStatus.HEALTHY,
    )

    signal_health = _signal_health()

    source_evaluator.evaluate.return_value = source_health
    signal_evaluator.evaluate.return_value = signal_health

    runtime = SignalHealthOperationalRuntime(
        source_transport_health_evaluator=source_evaluator,
        signal_health_evaluator=signal_evaluator,
    )

    measurement = _measurement()

    result = runtime.process(
        profile=_profile(),
        media_health=_media_health(),
        media_snapshot=_media_snapshot(
            source_type="futureSource",
        ),
        measurement=measurement,
    )

    assert result is signal_health

    source_evaluator.evaluate.assert_called_once_with(
        service_id="impact",
        source_type="futureSource",
        measurement=measurement.get_path("impact"),
    )

# ---------------------------------------------------------------------------
# ENG-013C — Media Health current-state freshness handoff
# ---------------------------------------------------------------------------


def test_runtime_uses_fresh_media_current_state() -> None:
    """Fresh current Media Health participates in Signal Health."""
    from datetime import timedelta

    from app.noc.current_state.media_health_current_state import (
        MediaHealthCurrentState,
    )
    from app.noc.current_state.media_health_current_state_resolver import (
        MediaHealthCurrentStateResolver,
    )
    from app.noc.current_state.media_health_freshness import (
        MediaHealthFreshnessPolicy,
    )

    profile = _profile()
    media_snapshot = _media_snapshot()
    measurement = _measurement()

    state = MediaHealthCurrentState(
        profile_id=profile.profile_id,
        service_id=profile.service_id,
        path_name=profile.path_name,
        observed_at=media_snapshot.captured_at - timedelta(seconds=8),
        health=_media_health(HealthStatus.HEALTHY),
    )

    runtime = SignalHealthOperationalRuntime(
        source_transport_health_evaluator=SourceTransportHealthEvaluator(),
        signal_health_evaluator=SignalHealthEvaluator(),
        media_health_current_state_resolver=(
            MediaHealthCurrentStateResolver(
                freshness_policy=MediaHealthFreshnessPolicy(
                    max_age_seconds=16.0,
                )
            )
        ),
    )

    result = runtime.process_current_state(
        profile=profile,
        media_current_state=state,
        media_snapshot=media_snapshot,
        measurement=measurement,
    )

    assert result.media_status is HealthStatus.HEALTHY
    assert result.status is HealthStatus.HEALTHY


def test_runtime_stale_media_current_state_becomes_unknown() -> None:
    """Stale Media Health is insufficient current evidence."""
    from datetime import timedelta

    from app.noc.current_state.media_health_current_state import (
        MediaHealthCurrentState,
    )
    from app.noc.current_state.media_health_current_state_resolver import (
        MediaHealthCurrentStateResolver,
    )
    from app.noc.current_state.media_health_freshness import (
        MediaHealthFreshnessPolicy,
    )

    profile = _profile()
    media_snapshot = _media_snapshot()
    measurement = _measurement()

    state = MediaHealthCurrentState(
        profile_id=profile.profile_id,
        service_id=profile.service_id,
        path_name=profile.path_name,
        observed_at=media_snapshot.captured_at - timedelta(seconds=17),
        health=_media_health(HealthStatus.HEALTHY),
    )

    runtime = SignalHealthOperationalRuntime(
        source_transport_health_evaluator=SourceTransportHealthEvaluator(),
        signal_health_evaluator=SignalHealthEvaluator(),
        media_health_current_state_resolver=(
            MediaHealthCurrentStateResolver(
                freshness_policy=MediaHealthFreshnessPolicy(
                    max_age_seconds=16.0,
                )
            )
        ),
    )

    result = runtime.process_current_state(
        profile=profile,
        media_current_state=state,
        media_snapshot=media_snapshot,
        measurement=measurement,
    )

    assert result.media_status is HealthStatus.UNKNOWN
    assert result.transport_status is HealthStatus.HEALTHY
    assert result.status is HealthStatus.UNKNOWN


def test_runtime_missing_media_current_state_becomes_unknown() -> None:
    """Missing Media current state must not produce synthetic HEALTHY."""
    from app.noc.current_state.media_health_current_state_resolver import (
        MediaHealthCurrentStateResolver,
    )
    from app.noc.current_state.media_health_freshness import (
        MediaHealthFreshnessPolicy,
    )

    profile = _profile()
    media_snapshot = _media_snapshot()
    measurement = _measurement()

    runtime = SignalHealthOperationalRuntime(
        source_transport_health_evaluator=SourceTransportHealthEvaluator(),
        signal_health_evaluator=SignalHealthEvaluator(),
        media_health_current_state_resolver=(
            MediaHealthCurrentStateResolver(
                freshness_policy=MediaHealthFreshnessPolicy(
                    max_age_seconds=16.0,
                )
            )
        ),
    )

    result = runtime.process_current_state(
        profile=profile,
        media_current_state=None,
        media_snapshot=media_snapshot,
        measurement=measurement,
    )

    assert result.media_status is HealthStatus.UNKNOWN
    assert result.transport_status is HealthStatus.HEALTHY
    assert result.status is HealthStatus.UNKNOWN


def test_runtime_negative_transport_dominates_stale_media() -> None:
    """Known negative transport evidence dominates stale Media UNKNOWN."""
    from datetime import timedelta

    from app.noc.current_state.media_health_current_state import (
        MediaHealthCurrentState,
    )
    from app.noc.current_state.media_health_current_state_resolver import (
        MediaHealthCurrentStateResolver,
    )
    from app.noc.current_state.media_health_freshness import (
        MediaHealthFreshnessPolicy,
    )

    profile = _profile()
    media_snapshot = _media_snapshot()

    base_measurement = _measurement()
    base_path = base_measurement.get_path("impact")

    zero_path = StreamingPathMeasurement(
        name=base_path.name,
        status=base_path.status,
        previous_status=base_path.previous_status,
        reader_count=base_path.reader_count,
        reader_delta=base_path.reader_delta,
        inbound_delta_bytes=0,
        outbound_delta_bytes=base_path.outbound_delta_bytes,
        inbound_bitrate_bps=0.0,
        outbound_bitrate_bps=base_path.outbound_bitrate_bps,
        state_changed=base_path.state_changed,
        quality=base_path.quality,
    )

    measurement = StreamingMeasurement(
        captured_at=base_measurement.captured_at,
        previous_captured_at=base_measurement.previous_captured_at,
        interval_seconds=base_measurement.interval_seconds,
        paths=(zero_path,),
        total_inbound_bitrate_bps=0.0,
        total_outbound_bitrate_bps=(
            base_measurement.total_outbound_bitrate_bps
        ),
        quality=base_measurement.quality,
    )

    state = MediaHealthCurrentState(
        profile_id=profile.profile_id,
        service_id=profile.service_id,
        path_name=profile.path_name,
        observed_at=media_snapshot.captured_at - timedelta(seconds=17),
        health=_media_health(HealthStatus.HEALTHY),
    )

    runtime = SignalHealthOperationalRuntime(
        source_transport_health_evaluator=SourceTransportHealthEvaluator(),
        signal_health_evaluator=SignalHealthEvaluator(),
        media_health_current_state_resolver=(
            MediaHealthCurrentStateResolver(
                freshness_policy=MediaHealthFreshnessPolicy(
                    max_age_seconds=16.0,
                )
            )
        ),
    )

    result = runtime.process_current_state(
        profile=profile,
        media_current_state=state,
        media_snapshot=media_snapshot,
        measurement=measurement,
    )

    assert result.media_status is HealthStatus.UNKNOWN
    assert result.transport_status is HealthStatus.DEGRADED
    assert result.status is HealthStatus.DEGRADED
