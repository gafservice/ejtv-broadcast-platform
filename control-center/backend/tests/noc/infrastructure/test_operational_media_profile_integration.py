"""Operational media profile integration.

This test proves that the real node configuration can be translated
into the canonical media contracts and evaluated through Media Health.

Physical ffprobe execution is intentionally excluded. The physical
boundary is covered independently by adapter tests and physical
validation.
"""

from datetime import datetime, timezone
from pathlib import Path

from app.domain.streaming.health import HealthStatus
from app.domain.streaming.media_evaluation import (
    MediaComparisonStatus,
    MediaEvaluator,
)
from app.domain.streaming.media_health import (
    MediaHealthEvaluator,
)
from app.domain.streaming.media_observation import (
    AudioTrackObservation,
    EvidenceAvailability,
    FrameRateObservation,
    InputMediaObservation,
    VideoTrackObservation,
)
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.infrastructure.node_media_profile_loader import (
    NodeMediaProfileLoader,
)
from app.services.media_health_stabilizer import (
    MediaHealthStabilizer,
)


OBSERVED_AT = datetime(
    2026,
    9,
    22,
    3,
    30,
    tzinfo=timezone.utc,
)

CONFIG_PATH = (
    Path(__file__).resolve().parents[4]
    / "config"
    / "nodes"
    / "ejtv-01.yaml"
)


def make_node_id() -> NodeId:
    return NodeId(
        id="ejtv-01",
        name="ejtv-01",
        display_name="EJTV 01",
        created_at=OBSERVED_AT,
    )


def test_operational_impact_profile_evaluates_healthy() -> None:
    profiles = NodeMediaProfileLoader().load(
        CONFIG_PATH
    )

    matching_profiles = [
        profile
        for profile in profiles
        if profile.service_id == "impact"
        and profile.path_name == "impact"
    ]

    assert len(matching_profiles) == 1

    profile = matching_profiles[0]

    assert profile.profile_id == "impact-main"

    observation = InputMediaObservation(
        node_id=make_node_id(),
        instance_id=NodeInstanceId(
            "ejtv-01-runtime"
        ),
        service_id="impact",
        path_name="impact",
        observed_at=OBSERVED_AT,
        container=None,
        video=VideoTrackObservation(
            availability=EvidenceAvailability.AVAILABLE,
            codec="h264",
            profile="Main",
            level="40",
            width=1920,
            height=1080,
            frame_rate=FrameRateObservation(
                numerator=30,
                denominator=1,
            ),
            gop=None,
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

    evaluation = MediaEvaluator().evaluate(
        profile=profile,
        observation=observation,
    )

    assert evaluation.container is None
    assert evaluation.video is not None
    assert evaluation.audio is not None

    assert (
        evaluation.video.presence_status
        is MediaComparisonStatus.MATCH
    )
    assert (
        evaluation.audio.presence_status
        is MediaComparisonStatus.MATCH
    )

    assert all(
        comparison.status
        is MediaComparisonStatus.MATCH
        for comparison
        in evaluation.video.comparisons
    )

    assert all(
        comparison.status
        is MediaComparisonStatus.MATCH
        for comparison
        in evaluation.audio.comparisons
    )

    health = MediaHealthEvaluator().evaluate(
        evaluation=evaluation,
    )

    assert health.status is HealthStatus.HEALTHY

    stable = MediaHealthStabilizer(
        degradation_seconds=0.0,
        recovery_seconds=0.0,
    ).stabilize(
        health,
        observed_at=OBSERVED_AT,
    )

    assert stable.status is HealthStatus.HEALTHY


def test_operational_policy_covers_all_reference_incoming_services() -> None:
    profiles = NodeMediaProfileLoader().load(
        CONFIG_PATH
    )

    profiles_by_identity = {
        (
            profile.profile_id,
            profile.service_id,
            profile.path_name,
        ): profile
        for profile in profiles
    }

    assert set(profiles_by_identity) == {
        ("impact-main", "impact", "impact"),
        ("ejtv-main", "ejtv", "ejtv"),
        ("enlace-main", "enlace", "enlace"),
    }

    for identity in (
        ("ejtv-main", "ejtv", "ejtv"),
        ("enlace-main", "enlace", "enlace"),
    ):
        profile = profiles_by_identity[identity]

        assert profile.container is None

        assert profile.video is not None
        assert profile.video.presence.value == "required"
        assert profile.video.codec == "hevc"
        assert profile.video.profile == "Main"
        assert profile.video.level == "120"
        assert profile.video.width == 1920
        assert profile.video.height == 1080
        assert profile.video.frame_rate_numerator == 30000
        assert profile.video.frame_rate_denominator == 1001

        assert profile.audio is not None
        assert profile.audio.presence.value == "required"
        assert profile.audio.codec == "aac"
        assert profile.audio.profile == "LC"
        assert profile.audio.sample_rate == 48000
        assert profile.audio.channels == 2
        assert profile.audio.channel_layout == "stereo"
