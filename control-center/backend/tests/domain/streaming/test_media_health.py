"""Contract tests for instantaneous Media Health.

ENG-013C — Contract 4

Media Health consumes MediaEvaluation and produces instantaneous
operational Health.

This contract does not stabilize temporal state, emit events or alarms,
or persist runtime state.
"""

from __future__ import annotations

import pytest

from app.domain.streaming.expected_media_profile import (
    MediaPresenceExpectation,
)
from app.domain.streaming.health import HealthStatus
from app.domain.streaming.media_evaluation import (
    MediaComparisonStatus,
    MediaComponentEvaluation,
    MediaEvaluation,
    MediaFieldEvaluation,
)
from app.domain.streaming.media_observation import (
    EvidenceAvailability,
)


def field(
    *,
    name: str,
    status: MediaComparisonStatus,
) -> MediaFieldEvaluation:
    return MediaFieldEvaluation(
        field_name=name,
        expected="expected",
        observed="observed",
        status=status,
    )


def component(
    *,
    name: str,
    presence_status: MediaComparisonStatus,
    comparisons: tuple[MediaFieldEvaluation, ...] = (),
) -> MediaComponentEvaluation:
    return MediaComponentEvaluation(
        component=name,
        presence_expectation=MediaPresenceExpectation.REQUIRED,
        evidence_availability=EvidenceAvailability.AVAILABLE,
        presence_status=presence_status,
        comparisons=comparisons,
    )


def evaluation(
    *,
    container: MediaComponentEvaluation | None = None,
    video: MediaComponentEvaluation | None = None,
    audio: MediaComponentEvaluation | None = None,
) -> MediaEvaluation:
    return MediaEvaluation(
        profile_id="impact-main",
        service_id="impact",
        path_name="impact",
        container=container,
        video=video,
        audio=audio,
    )


def test_media_health_reuses_canonical_health_status() -> None:
    from app.domain.streaming.media_health import (
        MediaComponentHealth,
        MediaHealth,
    )

    component_health = MediaComponentHealth(
        component="video",
        status=HealthStatus.HEALTHY,
    )

    health = MediaHealth(
        profile_id="impact-main",
        service_id="impact",
        path_name="impact",
        status=HealthStatus.HEALTHY,
        container=None,
        video=component_health,
        audio=None,
    )

    assert health.status is HealthStatus.HEALTHY
    assert health.video.status is HealthStatus.HEALTHY


def test_all_match_component_is_healthy() -> None:
    from app.domain.streaming.media_health import (
        MediaHealthEvaluator,
    )

    result = MediaHealthEvaluator().evaluate(
        evaluation=evaluation(
            video=component(
                name="video",
                presence_status=MediaComparisonStatus.MATCH,
                comparisons=(
                    field(
                        name="codec",
                        status=MediaComparisonStatus.MATCH,
                    ),
                    field(
                        name="width",
                        status=MediaComparisonStatus.MATCH,
                    ),
                ),
            ),
        )
    )

    assert result.video is not None
    assert result.video.status is HealthStatus.HEALTHY
    assert result.status is HealthStatus.HEALTHY


def test_component_mismatch_is_degraded_not_critical() -> None:
    from app.domain.streaming.media_health import (
        MediaHealthEvaluator,
    )

    result = MediaHealthEvaluator().evaluate(
        evaluation=evaluation(
            video=component(
                name="video",
                presence_status=MediaComparisonStatus.MATCH,
                comparisons=(
                    field(
                        name="codec",
                        status=MediaComparisonStatus.MISMATCH,
                    ),
                ),
            ),
        )
    )

    assert result.video is not None
    assert result.video.status is HealthStatus.DEGRADED
    assert result.video.status is not HealthStatus.CRITICAL
    assert result.status is HealthStatus.DEGRADED


def test_presence_mismatch_is_degraded_not_critical() -> None:
    from app.domain.streaming.media_health import (
        MediaHealthEvaluator,
    )

    result = MediaHealthEvaluator().evaluate(
        evaluation=evaluation(
            audio=component(
                name="audio",
                presence_status=MediaComparisonStatus.MISMATCH,
            ),
        )
    )

    assert result.audio is not None
    assert result.audio.status is HealthStatus.DEGRADED
    assert result.audio.status is not HealthStatus.CRITICAL
    assert result.status is HealthStatus.DEGRADED


def test_not_evaluated_without_mismatch_is_unknown() -> None:
    from app.domain.streaming.media_health import (
        MediaHealthEvaluator,
    )

    result = MediaHealthEvaluator().evaluate(
        evaluation=evaluation(
            audio=component(
                name="audio",
                presence_status=MediaComparisonStatus.MATCH,
                comparisons=(
                    field(
                        name="profile",
                        status=MediaComparisonStatus.NOT_EVALUATED,
                    ),
                ),
            ),
        )
    )

    assert result.audio is not None
    assert result.audio.status is HealthStatus.UNKNOWN
    assert result.status is HealthStatus.UNKNOWN


def test_mismatch_dominates_not_evaluated() -> None:
    from app.domain.streaming.media_health import (
        MediaHealthEvaluator,
    )

    result = MediaHealthEvaluator().evaluate(
        evaluation=evaluation(
            video=component(
                name="video",
                presence_status=MediaComparisonStatus.MATCH,
                comparisons=(
                    field(
                        name="codec",
                        status=MediaComparisonStatus.MISMATCH,
                    ),
                    field(
                        name="gop_interval_seconds",
                        status=MediaComparisonStatus.NOT_EVALUATED,
                    ),
                ),
            ),
        )
    )

    assert result.video is not None
    assert result.video.status is HealthStatus.DEGRADED
    assert result.status is HealthStatus.DEGRADED


def test_degraded_component_dominates_unknown_component() -> None:
    from app.domain.streaming.media_health import (
        MediaHealthEvaluator,
    )

    result = MediaHealthEvaluator().evaluate(
        evaluation=evaluation(
            video=component(
                name="video",
                presence_status=MediaComparisonStatus.MATCH,
                comparisons=(
                    field(
                        name="codec",
                        status=MediaComparisonStatus.MISMATCH,
                    ),
                ),
            ),
            audio=component(
                name="audio",
                presence_status=MediaComparisonStatus.MATCH,
                comparisons=(
                    field(
                        name="profile",
                        status=MediaComparisonStatus.NOT_EVALUATED,
                    ),
                ),
            ),
        )
    )

    assert result.video is not None
    assert result.audio is not None

    assert result.video.status is HealthStatus.DEGRADED
    assert result.audio.status is HealthStatus.UNKNOWN
    assert result.status is HealthStatus.DEGRADED


def test_missing_evaluation_component_is_not_invented() -> None:
    from app.domain.streaming.media_health import (
        MediaHealthEvaluator,
    )

    result = MediaHealthEvaluator().evaluate(
        evaluation=evaluation(
            video=component(
                name="video",
                presence_status=MediaComparisonStatus.MATCH,
            ),
        )
    )

    assert result.container is None
    assert result.video is not None
    assert result.audio is None
    assert result.status is HealthStatus.HEALTHY


def test_empty_media_evaluation_is_unknown() -> None:
    from app.domain.streaming.media_health import (
        MediaHealthEvaluator,
    )

    result = MediaHealthEvaluator().evaluate(
        evaluation=evaluation()
    )

    assert result.container is None
    assert result.video is None
    assert result.audio is None
    assert result.status is HealthStatus.UNKNOWN


def test_media_health_preserves_evaluation_identity() -> None:
    from app.domain.streaming.media_health import (
        MediaHealthEvaluator,
    )

    result = MediaHealthEvaluator().evaluate(
        evaluation=evaluation(
            container=component(
                name="container",
                presence_status=MediaComparisonStatus.MATCH,
            ),
        )
    )

    assert result.profile_id == "impact-main"
    assert result.service_id == "impact"
    assert result.path_name == "impact"


def test_media_health_evaluator_rejects_wrong_input_type() -> None:
    from app.domain.streaming.media_health import (
        MediaHealthEvaluator,
    )

    with pytest.raises(
        TypeError,
        match="MediaEvaluation",
    ):
        MediaHealthEvaluator().evaluate(
            evaluation=object(),
        )


# ---------------------------------------------------------------------------
# Permanent Contract 4 invariant coverage
# ---------------------------------------------------------------------------


def test_media_component_health_normalizes_component() -> None:
    from app.domain.streaming.media_health import (
        MediaComponentHealth,
    )

    result = MediaComponentHealth(
        component="  video  ",
        status=HealthStatus.HEALTHY,
    )

    assert result.component == "video"


@pytest.mark.parametrize(
    ("kwargs", "exception", "message"),
    (
        (
            {
                "component": "   ",
                "status": HealthStatus.HEALTHY,
            },
            ValueError,
            "component must not be blank",
        ),
        (
            {
                "component": "video",
                "status": "HEALTHY",
            },
            TypeError,
            "status must be a HealthStatus",
        ),
    ),
)
def test_media_component_health_rejects_invalid_values(
    kwargs,
    exception,
    message,
) -> None:
    from app.domain.streaming.media_health import (
        MediaComponentHealth,
    )

    with pytest.raises(exception, match=message):
        MediaComponentHealth(**kwargs)


def test_media_health_normalizes_identity() -> None:
    from app.domain.streaming.media_health import (
        MediaComponentHealth,
        MediaHealth,
    )

    result = MediaHealth(
        profile_id="  impact-main  ",
        service_id="  impact  ",
        path_name="  impact  ",
        status=HealthStatus.HEALTHY,
        video=MediaComponentHealth(
            component="video",
            status=HealthStatus.HEALTHY,
        ),
    )

    assert result.profile_id == "impact-main"
    assert result.service_id == "impact"
    assert result.path_name == "impact"


@pytest.mark.parametrize(
    ("kwargs", "exception", "message"),
    (
        (
            {
                "profile_id": " ",
                "service_id": "impact",
                "path_name": "impact",
                "status": HealthStatus.HEALTHY,
            },
            ValueError,
            "profile_id must not be blank",
        ),
        (
            {
                "profile_id": "impact-main",
                "service_id": " ",
                "path_name": "impact",
                "status": HealthStatus.HEALTHY,
            },
            ValueError,
            "service_id must not be blank",
        ),
        (
            {
                "profile_id": "impact-main",
                "service_id": "impact",
                "path_name": " ",
                "status": HealthStatus.HEALTHY,
            },
            ValueError,
            "path_name must not be blank",
        ),
        (
            {
                "profile_id": "impact-main",
                "service_id": "impact",
                "path_name": "impact",
                "status": "HEALTHY",
            },
            TypeError,
            "status must be a HealthStatus",
        ),
        (
            {
                "profile_id": "impact-main",
                "service_id": "impact",
                "path_name": "impact",
                "status": HealthStatus.HEALTHY,
                "video": object(),
            },
            TypeError,
            "video must be a MediaComponentHealth or None",
        ),
    ),
)
def test_media_health_rejects_invalid_values(
    kwargs,
    exception,
    message,
) -> None:
    from app.domain.streaming.media_health import (
        MediaHealth,
    )

    with pytest.raises(exception, match=message):
        MediaHealth(**kwargs)


@pytest.mark.parametrize(
    ("statuses", "expected"),
    (
        (
            (HealthStatus.HEALTHY,),
            HealthStatus.HEALTHY,
        ),
        (
            (HealthStatus.DEGRADED,),
            HealthStatus.DEGRADED,
        ),
        (
            (HealthStatus.UNKNOWN,),
            HealthStatus.UNKNOWN,
        ),
        (
            (
                HealthStatus.HEALTHY,
                HealthStatus.UNKNOWN,
            ),
            HealthStatus.UNKNOWN,
        ),
        (
            (
                HealthStatus.UNKNOWN,
                HealthStatus.HEALTHY,
            ),
            HealthStatus.UNKNOWN,
        ),
        (
            (
                HealthStatus.DEGRADED,
                HealthStatus.UNKNOWN,
            ),
            HealthStatus.DEGRADED,
        ),
        (
            (
                HealthStatus.UNKNOWN,
                HealthStatus.DEGRADED,
            ),
            HealthStatus.DEGRADED,
        ),
        (
            (
                HealthStatus.HEALTHY,
                HealthStatus.DEGRADED,
            ),
            HealthStatus.DEGRADED,
        ),
        (
            (),
            HealthStatus.UNKNOWN,
        ),
    ),
)
def test_media_health_aggregate_status_precedence(
    statuses,
    expected,
) -> None:
    from app.domain.streaming.media_health import (
        MediaHealthEvaluator,
    )

    result = MediaHealthEvaluator._aggregate_status(
        statuses
    )

    assert result is expected


@pytest.mark.parametrize(
    ("statuses", "expected"),
    (
        (
            (MediaComparisonStatus.MATCH,),
            HealthStatus.HEALTHY,
        ),
        (
            (MediaComparisonStatus.MISMATCH,),
            HealthStatus.DEGRADED,
        ),
        (
            (
                MediaComparisonStatus.NOT_EVALUATED,
            ),
            HealthStatus.UNKNOWN,
        ),
        (
            (
                MediaComparisonStatus.MATCH,
                MediaComparisonStatus.NOT_EVALUATED,
            ),
            HealthStatus.UNKNOWN,
        ),
        (
            (
                MediaComparisonStatus.MISMATCH,
                MediaComparisonStatus.NOT_EVALUATED,
            ),
            HealthStatus.DEGRADED,
        ),
        (
            (
                MediaComparisonStatus.NOT_EVALUATED,
                MediaComparisonStatus.MISMATCH,
            ),
            HealthStatus.DEGRADED,
        ),
    ),
)
def test_media_health_comparison_status_precedence(
    statuses,
    expected,
) -> None:
    from app.domain.streaming.media_health import (
        MediaHealthEvaluator,
    )

    result = MediaHealthEvaluator._status_from_comparisons(
        statuses
    )

    assert result is expected


def test_media_health_result_objects_are_frozen() -> None:
    from dataclasses import FrozenInstanceError

    from app.domain.streaming.media_health import (
        MediaComponentHealth,
        MediaHealth,
    )

    component_health = MediaComponentHealth(
        component="video",
        status=HealthStatus.HEALTHY,
    )

    health = MediaHealth(
        profile_id="impact-main",
        service_id="impact",
        path_name="impact",
        status=HealthStatus.HEALTHY,
        video=component_health,
    )

    with pytest.raises(FrozenInstanceError):
        component_health.status = HealthStatus.DEGRADED

    with pytest.raises(FrozenInstanceError):
        health.status = HealthStatus.DEGRADED


def test_media_health_domain_does_not_forbid_canonical_critical() -> None:
    from app.domain.streaming.media_health import (
        MediaHealth,
    )

    result = MediaHealth(
        profile_id="impact-main",
        service_id="impact",
        path_name="impact",
        status=HealthStatus.CRITICAL,
    )

    assert result.status is HealthStatus.CRITICAL


def test_media_health_evaluator_v1_does_not_produce_critical() -> None:
    from app.domain.streaming.media_health import (
        MediaHealthEvaluator,
    )

    result = MediaHealthEvaluator().evaluate(
        evaluation=evaluation(
            video=component(
                name="video",
                presence_status=MediaComparisonStatus.MISMATCH,
                comparisons=(
                    field(
                        name="codec",
                        status=MediaComparisonStatus.MISMATCH,
                    ),
                ),
            ),
        )
    )

    assert result.status is HealthStatus.DEGRADED
    assert result.status is not HealthStatus.CRITICAL
