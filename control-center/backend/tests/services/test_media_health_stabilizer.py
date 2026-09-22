from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.domain.streaming.health import HealthStatus
from app.domain.streaming.media_health import (
    MediaHealth,
)
from app.services.media_health_stabilizer import (
    MediaHealthStabilizer,
)


BASE_TIME = datetime(
    2026,
    9,
    22,
    2,
    0,
    tzinfo=timezone.utc,
)


def make_health(
    status: HealthStatus,
    *,
    profile_id: str = "ejtv-main",
    service_id: str = "ejtv",
    path_name: str | None = "ejtv",
) -> MediaHealth:
    return MediaHealth(
        profile_id=profile_id,
        service_id=service_id,
        path_name=path_name,
        status=status,
    )


def test_first_observation_becomes_stable_immediately() -> None:
    stabilizer = MediaHealthStabilizer(
        degradation_seconds=10.0,
        recovery_seconds=5.0,
    )

    health = make_health(HealthStatus.HEALTHY)

    result = stabilizer.stabilize(
        health,
        observed_at=BASE_TIME,
    )

    assert result is health


def test_brief_degradation_does_not_replace_healthy_state() -> None:
    stabilizer = MediaHealthStabilizer(
        degradation_seconds=10.0,
        recovery_seconds=5.0,
    )

    healthy = make_health(HealthStatus.HEALTHY)
    degraded = make_health(HealthStatus.DEGRADED)

    stabilizer.stabilize(
        healthy,
        observed_at=BASE_TIME,
    )

    result = stabilizer.stabilize(
        degraded,
        observed_at=BASE_TIME + timedelta(seconds=1),
    )

    assert result.status is HealthStatus.HEALTHY


def test_persistent_degradation_commits_after_confirmation() -> None:
    stabilizer = MediaHealthStabilizer(
        degradation_seconds=10.0,
        recovery_seconds=5.0,
    )

    stabilizer.stabilize(
        make_health(HealthStatus.HEALTHY),
        observed_at=BASE_TIME,
    )

    stabilizer.stabilize(
        make_health(HealthStatus.DEGRADED),
        observed_at=BASE_TIME + timedelta(seconds=1),
    )

    result = stabilizer.stabilize(
        make_health(HealthStatus.DEGRADED),
        observed_at=BASE_TIME + timedelta(seconds=11),
    )

    assert result.status is HealthStatus.DEGRADED


def test_recovery_requires_recovery_confirmation() -> None:
    stabilizer = MediaHealthStabilizer(
        degradation_seconds=0.0,
        recovery_seconds=5.0,
    )

    stabilizer.stabilize(
        make_health(HealthStatus.DEGRADED),
        observed_at=BASE_TIME,
    )

    pending = stabilizer.stabilize(
        make_health(HealthStatus.HEALTHY),
        observed_at=BASE_TIME + timedelta(seconds=1),
    )

    confirmed = stabilizer.stabilize(
        make_health(HealthStatus.HEALTHY),
        observed_at=BASE_TIME + timedelta(seconds=6),
    )

    assert pending.status is HealthStatus.DEGRADED
    assert confirmed.status is HealthStatus.HEALTHY


def test_brief_unknown_does_not_replace_known_stable_state() -> None:
    stabilizer = MediaHealthStabilizer(
        degradation_seconds=10.0,
        recovery_seconds=5.0,
    )

    stabilizer.stabilize(
        make_health(HealthStatus.HEALTHY),
        observed_at=BASE_TIME,
    )

    result = stabilizer.stabilize(
        make_health(HealthStatus.UNKNOWN),
        observed_at=BASE_TIME + timedelta(seconds=1),
    )

    assert result.status is HealthStatus.HEALTHY


def test_persistent_unknown_commits_after_degradation_window() -> None:
    stabilizer = MediaHealthStabilizer(
        degradation_seconds=10.0,
        recovery_seconds=5.0,
    )

    stabilizer.stabilize(
        make_health(HealthStatus.HEALTHY),
        observed_at=BASE_TIME,
    )

    stabilizer.stabilize(
        make_health(HealthStatus.UNKNOWN),
        observed_at=BASE_TIME + timedelta(seconds=1),
    )

    result = stabilizer.stabilize(
        make_health(HealthStatus.UNKNOWN),
        observed_at=BASE_TIME + timedelta(seconds=11),
    )

    assert result.status is HealthStatus.UNKNOWN


def test_candidate_is_cancelled_when_stable_state_returns() -> None:
    stabilizer = MediaHealthStabilizer(
        degradation_seconds=10.0,
        recovery_seconds=5.0,
    )

    stabilizer.stabilize(
        make_health(HealthStatus.HEALTHY),
        observed_at=BASE_TIME,
    )

    stabilizer.stabilize(
        make_health(HealthStatus.DEGRADED),
        observed_at=BASE_TIME + timedelta(seconds=1),
    )

    returned = stabilizer.stabilize(
        make_health(HealthStatus.HEALTHY),
        observed_at=BASE_TIME + timedelta(seconds=2),
    )

    later = stabilizer.stabilize(
        make_health(HealthStatus.DEGRADED),
        observed_at=BASE_TIME + timedelta(seconds=3),
    )

    assert returned.status is HealthStatus.HEALTHY
    assert later.status is HealthStatus.HEALTHY


def test_degraded_to_unknown_restarts_candidate_window() -> None:
    stabilizer = MediaHealthStabilizer(
        degradation_seconds=10.0,
        recovery_seconds=5.0,
    )

    stabilizer.stabilize(
        make_health(HealthStatus.HEALTHY),
        observed_at=BASE_TIME,
    )

    stabilizer.stabilize(
        make_health(HealthStatus.DEGRADED),
        observed_at=BASE_TIME + timedelta(seconds=1),
    )

    stabilizer.stabilize(
        make_health(HealthStatus.UNKNOWN),
        observed_at=BASE_TIME + timedelta(seconds=9),
    )

    result = stabilizer.stabilize(
        make_health(HealthStatus.UNKNOWN),
        observed_at=BASE_TIME + timedelta(seconds=11),
    )

    assert result.status is HealthStatus.HEALTHY


def test_unknown_to_degraded_restarts_candidate_window() -> None:
    stabilizer = MediaHealthStabilizer(
        degradation_seconds=10.0,
        recovery_seconds=5.0,
    )

    stabilizer.stabilize(
        make_health(HealthStatus.HEALTHY),
        observed_at=BASE_TIME,
    )

    stabilizer.stabilize(
        make_health(HealthStatus.UNKNOWN),
        observed_at=BASE_TIME + timedelta(seconds=1),
    )

    stabilizer.stabilize(
        make_health(HealthStatus.DEGRADED),
        observed_at=BASE_TIME + timedelta(seconds=9),
    )

    result = stabilizer.stabilize(
        make_health(HealthStatus.DEGRADED),
        observed_at=BASE_TIME + timedelta(seconds=11),
    )

    assert result.status is HealthStatus.HEALTHY


def test_out_of_order_observation_is_rejected() -> None:
    stabilizer = MediaHealthStabilizer(
        degradation_seconds=10.0,
        recovery_seconds=5.0,
    )

    stabilizer.stabilize(
        make_health(HealthStatus.HEALTHY),
        observed_at=BASE_TIME + timedelta(seconds=10),
    )

    with pytest.raises(ValueError):
        stabilizer.stabilize(
            make_health(HealthStatus.DEGRADED),
            observed_at=BASE_TIME + timedelta(seconds=9),
        )


def test_zero_degradation_delay_commits_immediately() -> None:
    stabilizer = MediaHealthStabilizer(
        degradation_seconds=0.0,
        recovery_seconds=5.0,
    )

    stabilizer.stabilize(
        make_health(HealthStatus.HEALTHY),
        observed_at=BASE_TIME,
    )

    result = stabilizer.stabilize(
        make_health(HealthStatus.DEGRADED),
        observed_at=BASE_TIME + timedelta(seconds=1),
    )

    assert result.status is HealthStatus.DEGRADED


def test_zero_recovery_delay_commits_immediately() -> None:
    stabilizer = MediaHealthStabilizer(
        degradation_seconds=10.0,
        recovery_seconds=0.0,
    )

    stabilizer.stabilize(
        make_health(HealthStatus.DEGRADED),
        observed_at=BASE_TIME,
    )

    result = stabilizer.stabilize(
        make_health(HealthStatus.HEALTHY),
        observed_at=BASE_TIME + timedelta(seconds=1),
    )

    assert result.status is HealthStatus.HEALTHY


def test_profiles_are_stabilized_independently() -> None:
    stabilizer = MediaHealthStabilizer(
        degradation_seconds=10.0,
        recovery_seconds=5.0,
    )

    stabilizer.stabilize(
        make_health(
            HealthStatus.HEALTHY,
            profile_id="profile-1",
            service_id="service-1",
            path_name="path-1",
        ),
        observed_at=BASE_TIME,
    )

    stabilizer.stabilize(
        make_health(
            HealthStatus.DEGRADED,
            profile_id="profile-1",
            service_id="service-1",
            path_name="path-1",
        ),
        observed_at=BASE_TIME + timedelta(seconds=1),
    )

    second = make_health(
        HealthStatus.DEGRADED,
        profile_id="profile-2",
        service_id="service-2",
        path_name="path-2",
    )

    result = stabilizer.stabilize(
        second,
        observed_at=BASE_TIME + timedelta(seconds=1),
    )

    assert result is second
    assert result.status is HealthStatus.DEGRADED


def test_negative_delays_are_rejected() -> None:
    with pytest.raises(ValueError):
        MediaHealthStabilizer(
            degradation_seconds=-1.0,
            recovery_seconds=5.0,
        )

    with pytest.raises(ValueError):
        MediaHealthStabilizer(
            degradation_seconds=10.0,
            recovery_seconds=-1.0,
        )


def test_wrong_health_type_is_rejected() -> None:
    stabilizer = MediaHealthStabilizer(
        degradation_seconds=10.0,
        recovery_seconds=5.0,
    )

    with pytest.raises(TypeError):
        stabilizer.stabilize(
            object(),  # type: ignore[arg-type]
            observed_at=BASE_TIME,
        )


def test_naive_observed_at_is_rejected() -> None:
    stabilizer = MediaHealthStabilizer(
        degradation_seconds=10.0,
        recovery_seconds=5.0,
    )

    with pytest.raises(ValueError):
        stabilizer.stabilize(
            make_health(HealthStatus.HEALTHY),
            observed_at=datetime(2026, 9, 22, 2, 0),
        )


def test_delay_arguments_reject_bool_and_non_numeric_values() -> None:
    invalid_cases = (
        {
            "degradation_seconds": True,
            "recovery_seconds": 5.0,
        },
        {
            "degradation_seconds": "10",
            "recovery_seconds": 5.0,
        },
        {
            "degradation_seconds": 10.0,
            "recovery_seconds": False,
        },
        {
            "degradation_seconds": 10.0,
            "recovery_seconds": "5",
        },
    )

    for kwargs in invalid_cases:
        with pytest.raises(TypeError):
            MediaHealthStabilizer(**kwargs)  # type: ignore[arg-type]


def test_equal_timestamp_is_allowed() -> None:
    stabilizer = MediaHealthStabilizer(
        degradation_seconds=10.0,
        recovery_seconds=5.0,
    )

    stabilizer.stabilize(
        make_health(HealthStatus.HEALTHY),
        observed_at=BASE_TIME,
    )

    result = stabilizer.stabilize(
        make_health(HealthStatus.DEGRADED),
        observed_at=BASE_TIME,
    )

    assert result.status is HealthStatus.HEALTHY


def test_degradation_commits_exactly_at_confirmation_boundary() -> None:
    stabilizer = MediaHealthStabilizer(
        degradation_seconds=10.0,
        recovery_seconds=5.0,
    )

    stabilizer.stabilize(
        make_health(HealthStatus.HEALTHY),
        observed_at=BASE_TIME,
    )

    stabilizer.stabilize(
        make_health(HealthStatus.DEGRADED),
        observed_at=BASE_TIME,
    )

    before = stabilizer.stabilize(
        make_health(HealthStatus.DEGRADED),
        observed_at=(
            BASE_TIME
            + timedelta(seconds=9, microseconds=999999)
        ),
    )

    boundary = stabilizer.stabilize(
        make_health(HealthStatus.DEGRADED),
        observed_at=BASE_TIME + timedelta(seconds=10),
    )

    assert before.status is HealthStatus.HEALTHY
    assert boundary.status is HealthStatus.DEGRADED


def test_exact_identity_reset_forgets_temporal_state() -> None:
    stabilizer = MediaHealthStabilizer(
        degradation_seconds=10.0,
        recovery_seconds=5.0,
    )

    stabilizer.stabilize(
        make_health(HealthStatus.HEALTHY),
        observed_at=BASE_TIME,
    )

    stabilizer.stabilize(
        make_health(HealthStatus.DEGRADED),
        observed_at=BASE_TIME + timedelta(seconds=1),
    )

    stabilizer.reset(
        profile_id="ejtv-main",
        service_id="ejtv",
        path_name="ejtv",
    )

    degraded = make_health(HealthStatus.DEGRADED)

    result = stabilizer.stabilize(
        degraded,
        observed_at=BASE_TIME + timedelta(seconds=2),
    )

    assert result is degraded
    assert result.status is HealthStatus.DEGRADED


def test_global_reset_forgets_all_temporal_state() -> None:
    stabilizer = MediaHealthStabilizer(
        degradation_seconds=10.0,
        recovery_seconds=5.0,
    )

    stabilizer.stabilize(
        make_health(HealthStatus.HEALTHY),
        observed_at=BASE_TIME,
    )

    stabilizer.reset()

    unknown = make_health(HealthStatus.UNKNOWN)

    result = stabilizer.stabilize(
        unknown,
        observed_at=BASE_TIME + timedelta(seconds=1),
    )

    assert result is unknown
    assert result.status is HealthStatus.UNKNOWN


def test_identity_includes_profile_service_and_path() -> None:
    stabilizer = MediaHealthStabilizer(
        degradation_seconds=10.0,
        recovery_seconds=5.0,
    )

    identities = (
        ("profile-1", "service", "path"),
        ("profile-2", "service", "path"),
        ("profile-1", "service", "other"),
        ("profile-1", "other", "path"),
        ("profile-1", "service", None),
    )

    for profile_id, service_id, path_name in identities:
        health = make_health(
            HealthStatus.DEGRADED,
            profile_id=profile_id,
            service_id=service_id,
            path_name=path_name,
        )

        result = stabilizer.stabilize(
            health,
            observed_at=BASE_TIME,
        )

        assert result is health
        assert result.status is HealthStatus.DEGRADED


def test_unknown_to_healthy_uses_recovery_window() -> None:
    stabilizer = MediaHealthStabilizer(
        degradation_seconds=10.0,
        recovery_seconds=5.0,
    )

    stabilizer.stabilize(
        make_health(HealthStatus.UNKNOWN),
        observed_at=BASE_TIME,
    )

    pending = stabilizer.stabilize(
        make_health(HealthStatus.HEALTHY),
        observed_at=BASE_TIME + timedelta(seconds=1),
    )

    confirmed = stabilizer.stabilize(
        make_health(HealthStatus.HEALTHY),
        observed_at=BASE_TIME + timedelta(seconds=6),
    )

    assert pending.status is HealthStatus.UNKNOWN
    assert confirmed.status is HealthStatus.HEALTHY


def test_manual_critical_uses_degradation_confirmation_window() -> None:
    stabilizer = MediaHealthStabilizer(
        degradation_seconds=10.0,
        recovery_seconds=5.0,
    )

    stabilizer.stabilize(
        make_health(HealthStatus.HEALTHY),
        observed_at=BASE_TIME,
    )

    pending = stabilizer.stabilize(
        make_health(HealthStatus.CRITICAL),
        observed_at=BASE_TIME + timedelta(seconds=1),
    )

    confirmed = stabilizer.stabilize(
        make_health(HealthStatus.CRITICAL),
        observed_at=BASE_TIME + timedelta(seconds=11),
    )

    assert pending.status is HealthStatus.HEALTHY
    assert confirmed.status is HealthStatus.CRITICAL


def test_held_status_preserves_current_component_evidence() -> None:
    from app.domain.streaming.media_health import MediaComponentHealth

    stabilizer = MediaHealthStabilizer(
        degradation_seconds=10.0,
        recovery_seconds=5.0,
    )

    healthy = MediaHealth(
        profile_id="profile",
        service_id="service",
        path_name="path",
        status=HealthStatus.HEALTHY,
        video=MediaComponentHealth(
            component="video",
            status=HealthStatus.HEALTHY,
        ),
    )

    degraded = MediaHealth(
        profile_id="profile",
        service_id="service",
        path_name="path",
        status=HealthStatus.DEGRADED,
        video=MediaComponentHealth(
            component="video",
            status=HealthStatus.DEGRADED,
        ),
    )

    stabilizer.stabilize(
        healthy,
        observed_at=BASE_TIME,
    )

    held = stabilizer.stabilize(
        degraded,
        observed_at=BASE_TIME + timedelta(seconds=1),
    )

    assert held.status is HealthStatus.HEALTHY
    assert held.video is degraded.video
    assert held.video is not None
    assert held.video.status is HealthStatus.DEGRADED


def test_real_media_contract_chain_is_temporally_stabilized() -> None:
    """Contract 1→5 integration using real domain objects."""

    from dataclasses import replace
    from datetime import datetime, timedelta, timezone

    from app.domain.streaming.expected_media_profile import (
        ExpectedAudioProfile,
        ExpectedContainerProfile,
        ExpectedMediaProfile,
        ExpectedVideoProfile,
        MediaPresenceExpectation,
    )
    from app.domain.streaming.media_evaluation import (
        MediaComparisonStatus,
        MediaEvaluator,
    )
    from app.domain.streaming.media_health import (
        MediaHealthEvaluator,
    )
    from app.domain.streaming.media_observation import (
        AudioTrackObservation,
        ContainerObservation,
        EvidenceAvailability,
        FrameRateObservation,
        InputMediaObservation,
        VideoTrackObservation,
    )
    from app.noc.domain.node_id import NodeId
    from app.noc.domain.node_instance import NodeInstanceId

    t0 = datetime(
        2026,
        9,
        22,
        6,
        0,
        tzinfo=timezone.utc,
    )

    profile = ExpectedMediaProfile(
        profile_id="impact-main",
        service_id="impact",
        path_name="impact",
        container=ExpectedContainerProfile(
            presence=MediaPresenceExpectation.REQUIRED,
            container_type="mpegts",
        ),
        video=ExpectedVideoProfile(
            presence=MediaPresenceExpectation.REQUIRED,
            codec="h264",
            profile="High",
            level="4.1",
            width=1920,
            height=1080,
            frame_rate_numerator=30000,
            frame_rate_denominator=1001,
        ),
        audio=ExpectedAudioProfile(
            presence=MediaPresenceExpectation.REQUIRED,
            codec="aac",
            profile="LC",
            sample_rate=48000,
            channels=2,
            channel_layout="stereo",
        ),
    )

    healthy_observation = InputMediaObservation(
        node_id=NodeId(
            id="ejtv-01",
            name="ejtv-01",
            display_name="EJTV 01",
            created_at=t0,
        ),
        instance_id=NodeInstanceId(
            "ejtv-01-runtime"
        ),
        service_id="impact",
        path_name="impact",
        observed_at=t0,
        container=ContainerObservation(
            availability=EvidenceAvailability.AVAILABLE,
            container_type="mpegts",
        ),
        video=VideoTrackObservation(
            availability=EvidenceAvailability.AVAILABLE,
            codec="h264",
            profile="High",
            level="4.1",
            width=1920,
            height=1080,
            frame_rate=FrameRateObservation(
                numerator=30000,
                denominator=1001,
            ),
        ),
        audio=AudioTrackObservation(
            availability=EvidenceAvailability.AVAILABLE,
            codec="aac",
            profile="LC",
            sample_rate=48000,
            channels=2,
            channel_layout="stereo",
        ),
    )

    media_evaluator = MediaEvaluator()
    health_evaluator = MediaHealthEvaluator()

    stabilizer = MediaHealthStabilizer(
        degradation_seconds=10.0,
        recovery_seconds=5.0,
    )

    # --------------------------------------------------------
    # Healthy observation traverses Contracts 1→5.
    # --------------------------------------------------------

    healthy_evaluation = media_evaluator.evaluate(
        profile=profile,
        observation=healthy_observation,
    )

    assert healthy_evaluation.video is not None

    assert (
        healthy_evaluation.video.presence_status
        is MediaComparisonStatus.MATCH
    )

    healthy_health = health_evaluator.evaluate(
        evaluation=healthy_evaluation,
    )

    assert healthy_health.status is HealthStatus.HEALTHY

    initial = stabilizer.stabilize(
        healthy_health,
        observed_at=healthy_observation.observed_at,
    )

    assert initial.status is HealthStatus.HEALTHY

    # --------------------------------------------------------
    # Real observation mismatch:
    # 1920×1080 -> 1280×720.
    # --------------------------------------------------------

    assert healthy_observation.video is not None

    degraded_observation = replace(
        healthy_observation,
        observed_at=t0 + timedelta(seconds=1),
        video=replace(
            healthy_observation.video,
            width=1280,
            height=720,
        ),
    )

    degraded_evaluation = media_evaluator.evaluate(
        profile=profile,
        observation=degraded_observation,
    )

    assert degraded_evaluation.video is not None

    mismatches = {
        comparison.field_name
        for comparison
        in degraded_evaluation.video.comparisons
        if (
            comparison.status
            is MediaComparisonStatus.MISMATCH
        )
    }

    assert mismatches == {
        "width",
        "height",
    }

    degraded_health = health_evaluator.evaluate(
        evaluation=degraded_evaluation,
    )

    assert degraded_health.status is HealthStatus.DEGRADED

    # Candidate begins at t0 + 1.
    held_degradation = stabilizer.stabilize(
        degraded_health,
        observed_at=degraded_observation.observed_at,
    )

    assert held_degradation.status is HealthStatus.HEALTHY

    # Same mismatch persists for ten seconds.
    persistent_observation = replace(
        degraded_observation,
        observed_at=t0 + timedelta(seconds=11),
    )

    persistent_evaluation = media_evaluator.evaluate(
        profile=profile,
        observation=persistent_observation,
    )

    persistent_health = health_evaluator.evaluate(
        evaluation=persistent_evaluation,
    )

    confirmed_degradation = stabilizer.stabilize(
        persistent_health,
        observed_at=persistent_observation.observed_at,
    )

    assert (
        confirmed_degradation.status
        is HealthStatus.DEGRADED
    )

    # --------------------------------------------------------
    # Healthy evidence returns.
    # Recovery requires five seconds.
    # --------------------------------------------------------

    recovery_observation = replace(
        healthy_observation,
        observed_at=t0 + timedelta(seconds=12),
    )

    recovery_evaluation = media_evaluator.evaluate(
        profile=profile,
        observation=recovery_observation,
    )

    recovery_health = health_evaluator.evaluate(
        evaluation=recovery_evaluation,
    )

    assert recovery_health.status is HealthStatus.HEALTHY

    held_recovery = stabilizer.stabilize(
        recovery_health,
        observed_at=recovery_observation.observed_at,
    )

    assert held_recovery.status is HealthStatus.DEGRADED

    confirmed_recovery_observation = replace(
        healthy_observation,
        observed_at=t0 + timedelta(seconds=17),
    )

    confirmed_recovery_evaluation = media_evaluator.evaluate(
        profile=profile,
        observation=confirmed_recovery_observation,
    )

    confirmed_recovery_health = health_evaluator.evaluate(
        evaluation=confirmed_recovery_evaluation,
    )

    confirmed_recovery = stabilizer.stabilize(
        confirmed_recovery_health,
        observed_at=confirmed_recovery_observation.observed_at,
    )

    assert confirmed_recovery.status is HealthStatus.HEALTHY
