"""Contract tests for stateless media evaluation.

ENG-013C — Contract 3

These tests intentionally precede the implementation.
Media evaluation compares declarative expectation with observed evidence.

It does NOT assign Health, severity, alarms, events or temporal state.
"""

from dataclasses import FrozenInstanceError

import pytest

from app.domain.streaming.media_observation import (
    EvidenceAvailability,
)
from app.domain.streaming.expected_media_profile import (
    MediaPresenceExpectation,
)


def test_media_evaluation_contract_imports() -> None:
    from app.domain.streaming.media_evaluation import (
        MediaComparisonStatus,
        MediaComponentEvaluation,
        MediaEvaluation,
        MediaFieldEvaluation,
    )

    assert MediaComparisonStatus.MATCH.value == "match"
    assert MediaComparisonStatus.MISMATCH.value == "mismatch"
    assert (
        MediaComparisonStatus.NOT_EVALUATED.value
        == "not_evaluated"
    )

    assert MediaFieldEvaluation is not None
    assert MediaComponentEvaluation is not None
    assert MediaEvaluation is not None


def test_comparison_status_is_not_health() -> None:
    from app.domain.streaming.media_evaluation import (
        MediaComparisonStatus,
    )

    values = {item.value for item in MediaComparisonStatus}

    assert values == {
        "match",
        "mismatch",
        "not_evaluated",
    }

    assert "healthy" not in values
    assert "degraded" not in values
    assert "critical" not in values


@pytest.mark.parametrize(
    (
        "presence",
        "availability",
        "expected_status",
    ),
    [
        (
            MediaPresenceExpectation.REQUIRED,
            EvidenceAvailability.AVAILABLE,
            "match",
        ),
        (
            MediaPresenceExpectation.REQUIRED,
            EvidenceAvailability.UNAVAILABLE,
            "mismatch",
        ),
        (
            MediaPresenceExpectation.REQUIRED,
            EvidenceAvailability.INSUFFICIENT,
            "not_evaluated",
        ),
        (
            MediaPresenceExpectation.REQUIRED,
            EvidenceAvailability.NOT_APPLICABLE,
            "not_evaluated",
        ),
        (
            MediaPresenceExpectation.OPTIONAL,
            EvidenceAvailability.AVAILABLE,
            "match",
        ),
        (
            MediaPresenceExpectation.OPTIONAL,
            EvidenceAvailability.UNAVAILABLE,
            "match",
        ),
        (
            MediaPresenceExpectation.OPTIONAL,
            EvidenceAvailability.INSUFFICIENT,
            "not_evaluated",
        ),
        (
            MediaPresenceExpectation.OPTIONAL,
            EvidenceAvailability.NOT_APPLICABLE,
            "not_evaluated",
        ),
        (
            MediaPresenceExpectation.FORBIDDEN,
            EvidenceAvailability.AVAILABLE,
            "mismatch",
        ),
        (
            MediaPresenceExpectation.FORBIDDEN,
            EvidenceAvailability.UNAVAILABLE,
            "match",
        ),
        (
            MediaPresenceExpectation.FORBIDDEN,
            EvidenceAvailability.INSUFFICIENT,
            "not_evaluated",
        ),
        (
            MediaPresenceExpectation.FORBIDDEN,
            EvidenceAvailability.NOT_APPLICABLE,
            "not_evaluated",
        ),
    ],
)
def test_presence_evaluation_semantics(
    presence: MediaPresenceExpectation,
    availability: EvidenceAvailability,
    expected_status: str,
) -> None:
    from app.domain.streaming.media_evaluation import (
        evaluate_presence,
    )

    result = evaluate_presence(
        presence=presence,
        availability=availability,
    )

    assert result.value == expected_status


def test_missing_component_observation_is_not_evaluated() -> None:
    from app.domain.streaming.media_evaluation import (
        evaluate_presence,
    )

    result = evaluate_presence(
        presence=MediaPresenceExpectation.REQUIRED,
        availability=None,
    )

    assert result.value == "not_evaluated"


def test_media_field_evaluation_preserves_evidence() -> None:
    from app.domain.streaming.media_evaluation import (
        MediaComparisonStatus,
        MediaFieldEvaluation,
    )

    evaluation = MediaFieldEvaluation(
        field_name="codec",
        expected="h264",
        observed="h265",
        status=MediaComparisonStatus.MISMATCH,
    )

    assert evaluation.field_name == "codec"
    assert evaluation.expected == "h264"
    assert evaluation.observed == "h265"
    assert (
        evaluation.status
        is MediaComparisonStatus.MISMATCH
    )


def test_media_field_evaluation_is_immutable() -> None:
    from app.domain.streaming.media_evaluation import (
        MediaComparisonStatus,
        MediaFieldEvaluation,
    )

    evaluation = MediaFieldEvaluation(
        field_name="codec",
        expected="h264",
        observed="h264",
        status=MediaComparisonStatus.MATCH,
    )

    with pytest.raises(FrozenInstanceError):
        evaluation.status = MediaComparisonStatus.MISMATCH


def test_component_evaluation_preserves_presence_and_availability() -> None:
    from app.domain.streaming.media_evaluation import (
        MediaComparisonStatus,
        MediaComponentEvaluation,
        MediaFieldEvaluation,
    )

    comparison = MediaFieldEvaluation(
        field_name="codec",
        expected="h264",
        observed="h264",
        status=MediaComparisonStatus.MATCH,
    )

    evaluation = MediaComponentEvaluation(
        component="video",
        presence_expectation=(
            MediaPresenceExpectation.REQUIRED
        ),
        evidence_availability=(
            EvidenceAvailability.AVAILABLE
        ),
        presence_status=MediaComparisonStatus.MATCH,
        comparisons=(comparison,),
    )

    assert evaluation.component == "video"
    assert (
        evaluation.presence_expectation
        is MediaPresenceExpectation.REQUIRED
    )
    assert (
        evaluation.evidence_availability
        is EvidenceAvailability.AVAILABLE
    )
    assert (
        evaluation.presence_status
        is MediaComparisonStatus.MATCH
    )
    assert evaluation.comparisons == (comparison,)


def test_component_evaluation_allows_missing_evidence_availability() -> None:
    from app.domain.streaming.media_evaluation import (
        MediaComparisonStatus,
        MediaComponentEvaluation,
    )

    evaluation = MediaComponentEvaluation(
        component="audio",
        presence_expectation=(
            MediaPresenceExpectation.REQUIRED
        ),
        evidence_availability=None,
        presence_status=(
            MediaComparisonStatus.NOT_EVALUATED
        ),
        comparisons=(),
    )

    assert evaluation.evidence_availability is None
    assert (
        evaluation.presence_status
        is MediaComparisonStatus.NOT_EVALUATED
    )


def test_media_evaluation_preserves_identity_and_components() -> None:
    from app.domain.streaming.media_evaluation import (
        MediaComparisonStatus,
        MediaComponentEvaluation,
        MediaEvaluation,
    )

    video = MediaComponentEvaluation(
        component="video",
        presence_expectation=(
            MediaPresenceExpectation.REQUIRED
        ),
        evidence_availability=(
            EvidenceAvailability.AVAILABLE
        ),
        presence_status=MediaComparisonStatus.MATCH,
        comparisons=(),
    )

    evaluation = MediaEvaluation(
        profile_id="impact-main",
        service_id="impact",
        path_name="impact",
        container=None,
        video=video,
        audio=None,
    )

    assert evaluation.profile_id == "impact-main"
    assert evaluation.service_id == "impact"
    assert evaluation.path_name == "impact"
    assert evaluation.container is None
    assert evaluation.video is video
    assert evaluation.audio is None


def test_media_evaluation_has_no_health_or_operational_state() -> None:
    from app.domain.streaming.media_evaluation import (
        MediaEvaluation,
    )

    evaluation = MediaEvaluation(
        profile_id="impact-main",
        service_id="impact",
        path_name="impact",
    )

    assert not hasattr(evaluation, "health")
    assert not hasattr(evaluation, "severity")
    assert not hasattr(evaluation, "alarm")
    assert not hasattr(evaluation, "event")
    assert not hasattr(evaluation, "candidate_since")


def test_evaluate_presence_rejects_invalid_presence_type() -> None:
    from app.domain.streaming.media_evaluation import (
        evaluate_presence,
    )

    with pytest.raises(
        TypeError,
        match="presence must be a MediaPresenceExpectation",
    ):
        evaluate_presence(
            presence="required",
            availability=EvidenceAvailability.AVAILABLE,
        )


def test_evaluate_presence_rejects_invalid_availability_type() -> None:
    from app.domain.streaming.media_evaluation import (
        evaluate_presence,
    )

    with pytest.raises(
        TypeError,
        match="availability must be EvidenceAvailability or None",
    ):
        evaluate_presence(
            presence=MediaPresenceExpectation.REQUIRED,
            availability="available",
        )


@pytest.mark.parametrize(
    "field_name",
    [
        "",
        " ",
        "   ",
    ],
)
def test_media_field_evaluation_rejects_blank_field_name(
    field_name: str,
) -> None:
    from app.domain.streaming.media_evaluation import (
        MediaComparisonStatus,
        MediaFieldEvaluation,
    )

    with pytest.raises(
        ValueError,
        match="field_name must not be blank",
    ):
        MediaFieldEvaluation(
            field_name=field_name,
            expected="h264",
            observed="h264",
            status=MediaComparisonStatus.MATCH,
        )


def test_media_field_evaluation_rejects_non_string_field_name() -> None:
    from app.domain.streaming.media_evaluation import (
        MediaComparisonStatus,
        MediaFieldEvaluation,
    )

    with pytest.raises(
        TypeError,
        match="field_name must be a str",
    ):
        MediaFieldEvaluation(
            field_name=123,
            expected="h264",
            observed="h264",
            status=MediaComparisonStatus.MATCH,
        )


def test_media_field_evaluation_normalizes_field_name() -> None:
    from app.domain.streaming.media_evaluation import (
        MediaComparisonStatus,
        MediaFieldEvaluation,
    )

    evaluation = MediaFieldEvaluation(
        field_name="  codec  ",
        expected="h264",
        observed="h264",
        status=MediaComparisonStatus.MATCH,
    )

    assert evaluation.field_name == "codec"


def test_media_field_evaluation_rejects_invalid_status() -> None:
    from app.domain.streaming.media_evaluation import (
        MediaFieldEvaluation,
    )

    with pytest.raises(
        TypeError,
        match="status must be a MediaComparisonStatus",
    ):
        MediaFieldEvaluation(
            field_name="codec",
            expected="h264",
            observed="h264",
            status="match",
        )


@pytest.mark.parametrize(
    "component",
    [
        "",
        " ",
        "   ",
    ],
)
def test_component_evaluation_rejects_blank_component(
    component: str,
) -> None:
    from app.domain.streaming.media_evaluation import (
        MediaComparisonStatus,
        MediaComponentEvaluation,
    )

    with pytest.raises(
        ValueError,
        match="component must not be blank",
    ):
        MediaComponentEvaluation(
            component=component,
            presence_expectation=(
                MediaPresenceExpectation.REQUIRED
            ),
            evidence_availability=(
                EvidenceAvailability.AVAILABLE
            ),
            presence_status=MediaComparisonStatus.MATCH,
        )


def test_component_evaluation_normalizes_component() -> None:
    from app.domain.streaming.media_evaluation import (
        MediaComparisonStatus,
        MediaComponentEvaluation,
    )

    evaluation = MediaComponentEvaluation(
        component="  video  ",
        presence_expectation=(
            MediaPresenceExpectation.REQUIRED
        ),
        evidence_availability=(
            EvidenceAvailability.AVAILABLE
        ),
        presence_status=MediaComparisonStatus.MATCH,
    )

    assert evaluation.component == "video"


def test_component_evaluation_rejects_invalid_presence_expectation() -> None:
    from app.domain.streaming.media_evaluation import (
        MediaComparisonStatus,
        MediaComponentEvaluation,
    )

    with pytest.raises(
        TypeError,
        match="presence_expectation",
    ):
        MediaComponentEvaluation(
            component="video",
            presence_expectation="required",
            evidence_availability=(
                EvidenceAvailability.AVAILABLE
            ),
            presence_status=MediaComparisonStatus.MATCH,
        )


def test_component_evaluation_rejects_invalid_evidence_availability() -> None:
    from app.domain.streaming.media_evaluation import (
        MediaComparisonStatus,
        MediaComponentEvaluation,
    )

    with pytest.raises(
        TypeError,
        match="evidence_availability",
    ):
        MediaComponentEvaluation(
            component="video",
            presence_expectation=(
                MediaPresenceExpectation.REQUIRED
            ),
            evidence_availability="available",
            presence_status=MediaComparisonStatus.MATCH,
        )


def test_component_evaluation_rejects_invalid_presence_status() -> None:
    from app.domain.streaming.media_evaluation import (
        MediaComponentEvaluation,
    )

    with pytest.raises(
        TypeError,
        match="presence_status",
    ):
        MediaComponentEvaluation(
            component="video",
            presence_expectation=(
                MediaPresenceExpectation.REQUIRED
            ),
            evidence_availability=(
                EvidenceAvailability.AVAILABLE
            ),
            presence_status="match",
        )


def test_component_evaluation_rejects_non_tuple_comparisons() -> None:
    from app.domain.streaming.media_evaluation import (
        MediaComparisonStatus,
        MediaComponentEvaluation,
    )

    with pytest.raises(
        TypeError,
        match="comparisons must be a tuple",
    ):
        MediaComponentEvaluation(
            component="video",
            presence_expectation=(
                MediaPresenceExpectation.REQUIRED
            ),
            evidence_availability=(
                EvidenceAvailability.AVAILABLE
            ),
            presence_status=MediaComparisonStatus.MATCH,
            comparisons=[],
        )


def test_component_evaluation_rejects_invalid_comparison_member() -> None:
    from app.domain.streaming.media_evaluation import (
        MediaComparisonStatus,
        MediaComponentEvaluation,
    )

    with pytest.raises(
        TypeError,
        match="contain MediaFieldEvaluation",
    ):
        MediaComponentEvaluation(
            component="video",
            presence_expectation=(
                MediaPresenceExpectation.REQUIRED
            ),
            evidence_availability=(
                EvidenceAvailability.AVAILABLE
            ),
            presence_status=MediaComparisonStatus.MATCH,
            comparisons=("not-an-evaluation",),
        )


@pytest.mark.parametrize(
    "field_name",
    [
        "profile_id",
        "service_id",
    ],
)
def test_media_evaluation_rejects_non_string_required_identity(
    field_name: str,
) -> None:
    from app.domain.streaming.media_evaluation import (
        MediaEvaluation,
    )

    kwargs = {
        "profile_id": "impact-main",
        "service_id": "impact",
    }
    kwargs[field_name] = 123

    with pytest.raises(
        TypeError,
        match=rf"{field_name} must be a str",
    ):
        MediaEvaluation(**kwargs)


@pytest.mark.parametrize(
    "field_name",
    [
        "profile_id",
        "service_id",
    ],
)
def test_media_evaluation_rejects_blank_required_identity(
    field_name: str,
) -> None:
    from app.domain.streaming.media_evaluation import (
        MediaEvaluation,
    )

    kwargs = {
        "profile_id": "impact-main",
        "service_id": "impact",
    }
    kwargs[field_name] = "   "

    with pytest.raises(
        ValueError,
        match=rf"{field_name} must not be blank",
    ):
        MediaEvaluation(**kwargs)


def test_media_evaluation_normalizes_identity() -> None:
    from app.domain.streaming.media_evaluation import (
        MediaEvaluation,
    )

    evaluation = MediaEvaluation(
        profile_id="  impact-main  ",
        service_id="  impact  ",
        path_name="  impact  ",
    )

    assert evaluation.profile_id == "impact-main"
    assert evaluation.service_id == "impact"
    assert evaluation.path_name == "impact"


def test_media_evaluation_rejects_non_string_path_name() -> None:
    from app.domain.streaming.media_evaluation import (
        MediaEvaluation,
    )

    with pytest.raises(
        TypeError,
        match="path_name must be str or None",
    ):
        MediaEvaluation(
            profile_id="impact-main",
            service_id="impact",
            path_name=123,
        )


def test_media_evaluation_rejects_blank_path_name() -> None:
    from app.domain.streaming.media_evaluation import (
        MediaEvaluation,
    )

    with pytest.raises(
        ValueError,
        match="path_name must not be blank",
    ):
        MediaEvaluation(
            profile_id="impact-main",
            service_id="impact",
            path_name="   ",
        )


@pytest.mark.parametrize(
    "field_name",
    [
        "container",
        "video",
        "audio",
    ],
)
def test_media_evaluation_rejects_invalid_component_type(
    field_name: str,
) -> None:
    from app.domain.streaming.media_evaluation import (
        MediaEvaluation,
    )

    kwargs = {
        "profile_id": "impact-main",
        "service_id": "impact",
        field_name: "invalid-component",
    }

    with pytest.raises(
        TypeError,
        match=rf"{field_name} must be MediaComponentEvaluation or None",
    ):
        MediaEvaluation(**kwargs)


# ---------------------------------------------------------------------------
# Stateless MediaEvaluator contract
# ---------------------------------------------------------------------------


def test_media_evaluator_matches_complete_available_profile() -> None:
    from app.domain.streaming.expected_media_profile import (
        ExpectedAudioProfile,
        ExpectedContainerProfile,
        ExpectedMediaProfile,
        ExpectedVideoProfile,
    )
    from app.domain.streaming.media_evaluation import (
        MediaComparisonStatus,
        MediaEvaluator,
    )
    from app.domain.streaming.media_observation import (
        AudioTrackObservation,
        ContainerObservation,
        FrameRateObservation,
        InputMediaObservation,
        VideoTrackObservation,
    )
    from app.noc.domain.node_id import NodeId
    from app.noc.domain.node_instance import NodeInstanceId
    from datetime import datetime, timezone

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

    observation = InputMediaObservation(
        node_id=NodeId(
            id="ejtv-01",
            name="ejtv-01",
            display_name="EJTV 01",
            created_at=datetime(
                2026,
                9,
                22,
                6,
                0,
                tzinfo=timezone.utc,
            ),
        ),
        instance_id=NodeInstanceId("ejtv-01-runtime"),
        service_id="impact",
        path_name="impact",
        observed_at=datetime(
            2026,
            9,
            22,
            6,
            0,
            tzinfo=timezone.utc,
        ),
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

    evaluation = MediaEvaluator().evaluate(
        profile=profile,
        observation=observation,
    )

    assert evaluation.profile_id == "impact-main"
    assert evaluation.service_id == "impact"
    assert evaluation.path_name == "impact"

    assert (
        evaluation.container.presence_status
        is MediaComparisonStatus.MATCH
    )
    assert (
        evaluation.video.presence_status
        is MediaComparisonStatus.MATCH
    )
    assert (
        evaluation.audio.presence_status
        is MediaComparisonStatus.MATCH
    )

    assert all(
        comparison.status is MediaComparisonStatus.MATCH
        for comparison in evaluation.container.comparisons
    )

    assert all(
        comparison.status is MediaComparisonStatus.MATCH
        for comparison in evaluation.video.comparisons
    )

    assert all(
        comparison.status is MediaComparisonStatus.MATCH
        for comparison in evaluation.audio.comparisons
    )


def test_media_evaluator_detects_descriptive_mismatch() -> None:
    from app.domain.streaming.expected_media_profile import (
        ExpectedMediaProfile,
        ExpectedVideoProfile,
    )
    from app.domain.streaming.media_evaluation import (
        MediaComparisonStatus,
        MediaEvaluator,
    )
    from app.domain.streaming.media_observation import (
        InputMediaObservation,
        VideoTrackObservation,
    )
    from app.noc.domain.node_id import NodeId
    from app.noc.domain.node_instance import NodeInstanceId
    from datetime import datetime, timezone

    profile = ExpectedMediaProfile(
        profile_id="impact-main",
        service_id="impact",
        video=ExpectedVideoProfile(
            presence=MediaPresenceExpectation.REQUIRED,
            codec="h264",
            width=1920,
            height=1080,
        ),
    )

    observation = InputMediaObservation(
        node_id=NodeId(
            id="ejtv-01",
            name="ejtv-01",
            display_name="EJTV 01",
            created_at=datetime(
                2026,
                9,
                22,
                6,
                0,
                tzinfo=timezone.utc,
            ),
        ),
        instance_id=NodeInstanceId("ejtv-01-runtime"),
        service_id="impact",
        observed_at=datetime(
            2026,
            9,
            22,
            6,
            0,
            tzinfo=timezone.utc,
        ),
        video=VideoTrackObservation(
            availability=EvidenceAvailability.AVAILABLE,
            codec="hevc",
            width=1280,
            height=720,
        ),
    )

    evaluation = MediaEvaluator().evaluate(
        profile=profile,
        observation=observation,
    )

    statuses = {
        item.field_name: item.status
        for item in evaluation.video.comparisons
    }

    assert statuses["codec"] is MediaComparisonStatus.MISMATCH
    assert statuses["width"] is MediaComparisonStatus.MISMATCH
    assert statuses["height"] is MediaComparisonStatus.MISMATCH


def test_media_evaluator_marks_missing_field_evidence_not_evaluated() -> None:
    from app.domain.streaming.expected_media_profile import (
        ExpectedAudioProfile,
        ExpectedMediaProfile,
    )
    from app.domain.streaming.media_evaluation import (
        MediaComparisonStatus,
        MediaEvaluator,
    )
    from app.domain.streaming.media_observation import (
        AudioTrackObservation,
        InputMediaObservation,
    )
    from app.noc.domain.node_id import NodeId
    from app.noc.domain.node_instance import NodeInstanceId
    from datetime import datetime, timezone

    profile = ExpectedMediaProfile(
        profile_id="impact-main",
        service_id="impact",
        audio=ExpectedAudioProfile(
            presence=MediaPresenceExpectation.REQUIRED,
            codec="aac",
            profile="LC",
            sample_rate=48000,
            channels=2,
            channel_layout="stereo",
        ),
    )

    observation = InputMediaObservation(
        node_id=NodeId(
            id="ejtv-01",
            name="ejtv-01",
            display_name="EJTV 01",
            created_at=datetime(
                2026,
                9,
                22,
                6,
                0,
                tzinfo=timezone.utc,
            ),
        ),
        instance_id=NodeInstanceId("ejtv-01-runtime"),
        service_id="impact",
        observed_at=datetime(
            2026,
            9,
            22,
            6,
            0,
            tzinfo=timezone.utc,
        ),
        audio=AudioTrackObservation(
            availability=EvidenceAvailability.AVAILABLE,
            codec="aac",
            profile=None,
            sample_rate=None,
            channels=None,
            channel_layout=None,
        ),
    )

    evaluation = MediaEvaluator().evaluate(
        profile=profile,
        observation=observation,
    )

    statuses = {
        item.field_name: item.status
        for item in evaluation.audio.comparisons
    }

    assert statuses["codec"] is MediaComparisonStatus.MATCH

    assert (
        statuses["profile"]
        is MediaComparisonStatus.NOT_EVALUATED
    )
    assert (
        statuses["sample_rate"]
        is MediaComparisonStatus.NOT_EVALUATED
    )
    assert (
        statuses["channels"]
        is MediaComparisonStatus.NOT_EVALUATED
    )
    assert (
        statuses["channel_layout"]
        is MediaComparisonStatus.NOT_EVALUATED
    )


def test_media_evaluator_compares_frame_rate_as_exact_rational() -> None:
    from app.domain.streaming.expected_media_profile import (
        ExpectedMediaProfile,
        ExpectedVideoProfile,
    )
    from app.domain.streaming.media_evaluation import (
        MediaComparisonStatus,
        MediaEvaluator,
    )
    from app.domain.streaming.media_observation import (
        FrameRateObservation,
        InputMediaObservation,
        VideoTrackObservation,
    )
    from app.noc.domain.node_id import NodeId
    from app.noc.domain.node_instance import NodeInstanceId
    from datetime import datetime, timezone

    profile = ExpectedMediaProfile(
        profile_id="impact-main",
        service_id="impact",
        video=ExpectedVideoProfile(
            presence=MediaPresenceExpectation.REQUIRED,
            frame_rate_numerator=30000,
            frame_rate_denominator=1001,
        ),
    )

    observation = InputMediaObservation(
        node_id=NodeId(
            id="ejtv-01",
            name="ejtv-01",
            display_name="EJTV 01",
            created_at=datetime(
                2026,
                9,
                22,
                6,
                0,
                tzinfo=timezone.utc,
            ),
        ),
        instance_id=NodeInstanceId("ejtv-01-runtime"),
        service_id="impact",
        observed_at=datetime(
            2026,
            9,
            22,
            6,
            0,
            tzinfo=timezone.utc,
        ),
        video=VideoTrackObservation(
            availability=EvidenceAvailability.AVAILABLE,
            frame_rate=FrameRateObservation(
                numerator=30000,
                denominator=1001,
            ),
        ),
    )

    evaluation = MediaEvaluator().evaluate(
        profile=profile,
        observation=observation,
    )

    statuses = {
        item.field_name: item.status
        for item in evaluation.video.comparisons
    }

    assert (
        statuses["frame_rate"]
        is MediaComparisonStatus.MATCH
    )


def test_media_evaluator_does_not_invent_gop_comparison_semantics() -> None:
    from app.domain.streaming.expected_media_profile import (
        ExpectedMediaProfile,
        ExpectedVideoProfile,
    )
    from app.domain.streaming.media_evaluation import (
        MediaComparisonStatus,
        MediaEvaluator,
    )
    from app.domain.streaming.media_observation import (
        GOPObservation,
        InputMediaObservation,
        VideoTrackObservation,
    )
    from app.noc.domain.node_id import NodeId
    from app.noc.domain.node_instance import NodeInstanceId
    from datetime import datetime, timezone

    profile = ExpectedMediaProfile(
        profile_id="impact-main",
        service_id="impact",
        video=ExpectedVideoProfile(
            presence=MediaPresenceExpectation.REQUIRED,
            gop_interval_seconds=2.0,
        ),
    )

    observation = InputMediaObservation(
        node_id=NodeId(
            id="ejtv-01",
            name="ejtv-01",
            display_name="EJTV 01",
            created_at=datetime(
                2026,
                9,
                22,
                6,
                0,
                tzinfo=timezone.utc,
            ),
        ),
        instance_id=NodeInstanceId("ejtv-01-runtime"),
        service_id="impact",
        observed_at=datetime(
            2026,
            9,
            22,
            6,
            0,
            tzinfo=timezone.utc,
        ),
        video=VideoTrackObservation(
            availability=EvidenceAvailability.AVAILABLE,
            gop=GOPObservation(
                availability=EvidenceAvailability.INSUFFICIENT,
                observed_frame_count=30,
                keyframe_count=1,
                i_frame_count=1,
                p_frame_count=29,
                b_frame_count=0,
                interval_count=0,
            ),
        ),
    )

    evaluation = MediaEvaluator().evaluate(
        profile=profile,
        observation=observation,
    )

    statuses = {
        item.field_name: item.status
        for item in evaluation.video.comparisons
    }

    assert (
        statuses["gop_interval_seconds"]
        is MediaComparisonStatus.NOT_EVALUATED
    )


# ---------------------------------------------------------------------------
# MediaEvaluator identity contract
# ---------------------------------------------------------------------------


def _make_media_evaluation_identity_observation(
    *,
    service_id: str = "impact",
    path_name: str | None = "impact",
):
    from datetime import datetime, timezone

    from app.domain.streaming.media_observation import (
        InputMediaObservation,
    )
    from app.noc.domain.node_id import NodeId
    from app.noc.domain.node_instance import NodeInstanceId

    observed_at = datetime(
        2026,
        9,
        22,
        6,
        0,
        tzinfo=timezone.utc,
    )

    return InputMediaObservation(
        node_id=NodeId(
            id="ejtv-01",
            name="ejtv-01",
            display_name="EJTV 01",
            created_at=observed_at,
        ),
        instance_id=NodeInstanceId(
            "ejtv-01-runtime"
        ),
        service_id=service_id,
        path_name=path_name,
        observed_at=observed_at,
    )


def test_media_evaluator_rejects_wrong_service_identity() -> None:
    from app.domain.streaming.expected_media_profile import (
        ExpectedMediaProfile,
    )
    from app.domain.streaming.media_evaluation import (
        MediaEvaluator,
    )

    profile = ExpectedMediaProfile(
        profile_id="impact-main",
        service_id="impact",
        path_name="impact",
    )

    observation = (
        _make_media_evaluation_identity_observation(
            service_id="enlace",
            path_name="impact",
        )
    )

    with pytest.raises(
        ValueError,
        match="service_id",
    ):
        MediaEvaluator().evaluate(
            profile=profile,
            observation=observation,
        )


def test_media_evaluator_rejects_wrong_explicit_path_identity() -> None:
    from app.domain.streaming.expected_media_profile import (
        ExpectedMediaProfile,
    )
    from app.domain.streaming.media_evaluation import (
        MediaEvaluator,
    )

    profile = ExpectedMediaProfile(
        profile_id="impact-main",
        service_id="impact",
        path_name="impact",
    )

    observation = (
        _make_media_evaluation_identity_observation(
            service_id="impact",
            path_name="enlace",
        )
    )

    with pytest.raises(
        ValueError,
        match="path_name",
    ):
        MediaEvaluator().evaluate(
            profile=profile,
            observation=observation,
        )


def test_media_evaluator_allows_profile_without_path_restriction() -> None:
    from app.domain.streaming.expected_media_profile import (
        ExpectedMediaProfile,
    )
    from app.domain.streaming.media_evaluation import (
        MediaEvaluator,
    )

    profile = ExpectedMediaProfile(
        profile_id="impact-main",
        service_id="impact",
        path_name=None,
    )

    observation = (
        _make_media_evaluation_identity_observation(
            service_id="impact",
            path_name="impact",
        )
    )

    evaluation = MediaEvaluator().evaluate(
        profile=profile,
        observation=observation,
    )

    assert evaluation.profile_id == "impact-main"
    assert evaluation.service_id == "impact"
    assert evaluation.path_name is None
