"""Tests for critical multimedia path availability evaluation."""

from datetime import UTC, datetime

import pytest

from app.domain.streaming.models import (
    MediaMTXSnapshot,
    MediaPath,
    MediaPathStatus,
    MediaSource,
)
from app.noc.domain.critical_path_policy import (
    CriticalPathPolicy,
)
from app.noc.services.critical_path_availability_evaluator import (
    CriticalPathAvailabilityEvaluation,
    CriticalPathAvailabilityEvaluator,
    CriticalPathAvailabilityState,
)


TIMESTAMP = datetime(
    2026,
    8,
    30,
    4,
    0,
    tzinfo=UTC,
)


def build_policy(
    *,
    path: str = "ejtv",
    enabled: bool = True,
) -> CriticalPathPolicy:
    return CriticalPathPolicy(
        path=path,
        enabled=enabled,
    )


def build_path(
    *,
    name: str = "ejtv",
    status: MediaPathStatus = MediaPathStatus.ACTIVE,
    source: MediaSource | None = None,
    ready: bool = True,
    available: bool = True,
    online: bool = True,
) -> MediaPath:
    if source is None and status is MediaPathStatus.ACTIVE:
        source = MediaSource(
            source_type="mpegtsSource",
        )

    return MediaPath(
        name=name,
        configuration_name=name,
        status=status,
        ready=ready,
        available=available,
        online=online,
        source=source,
    )


def build_snapshot(
    *paths: MediaPath,
) -> MediaMTXSnapshot:
    return MediaMTXSnapshot(
        captured_at=TIMESTAMP,
        paths=tuple(paths),
        reported_item_count=len(paths),
        reported_page_count=1,
    )


def test_state_string_representation() -> None:
    assert str(
        CriticalPathAvailabilityState.AVAILABLE
    ) == "AVAILABLE"

    assert str(
        CriticalPathAvailabilityState.UNAVAILABLE
    ) == "UNAVAILABLE"


def test_active_source_path_is_available() -> None:
    path = build_path()

    result = CriticalPathAvailabilityEvaluator().evaluate(
        snapshot=build_snapshot(path),
        policies=(build_policy(),),
    )

    assert len(result) == 1
    assert (
        result[0].state
        is CriticalPathAvailabilityState.AVAILABLE
    )
    assert result[0].media_path is path


def test_missing_path_is_unavailable() -> None:
    result = CriticalPathAvailabilityEvaluator().evaluate(
        snapshot=build_snapshot(),
        policies=(build_policy(),),
    )

    assert (
        result[0].state
        is CriticalPathAvailabilityState.UNAVAILABLE
    )
    assert result[0].media_path is None


def test_no_source_path_is_unavailable() -> None:
    path = MediaPath(
        name="ejtv",
        configuration_name="ejtv",
        status=MediaPathStatus.NO_SOURCE,
        ready=False,
        available=False,
        online=False,
        source=None,
    )

    result = CriticalPathAvailabilityEvaluator().evaluate(
        snapshot=build_snapshot(path),
        policies=(build_policy(),),
    )

    assert (
        result[0].state
        is CriticalPathAvailabilityState.UNAVAILABLE
    )
    assert result[0].media_path is path


def test_offline_path_is_unavailable() -> None:
    path = build_path(
        status=MediaPathStatus.OFFLINE,
        source=MediaSource(source_type="mpegtsSource"),
        ready=False,
        available=False,
        online=False,
    )

    result = CriticalPathAvailabilityEvaluator().evaluate(
        snapshot=build_snapshot(path),
        policies=(build_policy(),),
    )

    assert (
        result[0].state
        is CriticalPathAvailabilityState.UNAVAILABLE
    )


@pytest.mark.parametrize(
    ("ready", "available", "online"),
    (
        (False, True, True),
        (True, False, True),
        (True, True, False),
    ),
)
def test_incomplete_operational_flags_are_unavailable(
    ready: bool,
    available: bool,
    online: bool,
) -> None:
    path = build_path(
        ready=ready,
        available=available,
        online=online,
    )

    result = CriticalPathAvailabilityEvaluator().evaluate(
        snapshot=build_snapshot(path),
        policies=(build_policy(),),
    )

    assert (
        result[0].state
        is CriticalPathAvailabilityState.UNAVAILABLE
    )


def test_active_path_without_source_is_unavailable() -> None:
    path = MediaPath(
        name="ejtv",
        configuration_name="ejtv",
        status=MediaPathStatus.ACTIVE,
        ready=True,
        available=True,
        online=True,
        source=None,
    )

    result = CriticalPathAvailabilityEvaluator().evaluate(
        snapshot=build_snapshot(path),
        policies=(build_policy(),),
    )

    assert (
        result[0].state
        is CriticalPathAvailabilityState.UNAVAILABLE
    )


def test_disabled_policy_is_not_evaluated() -> None:
    result = CriticalPathAvailabilityEvaluator().evaluate(
        snapshot=build_snapshot(build_path()),
        policies=(build_policy(enabled=False),),
    )

    assert result == ()


def test_multiple_policies_are_sorted_by_path() -> None:
    result = CriticalPathAvailabilityEvaluator().evaluate(
        snapshot=build_snapshot(),
        policies=(
            build_policy(path="z-path"),
            build_policy(path="a-path"),
        ),
    )

    assert tuple(
        evaluation.policy.path
        for evaluation in result
    ) == (
        "a-path",
        "z-path",
    )


def test_duplicate_paths_are_rejected() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "policies must not contain duplicate "
            "path values"
        ),
    ):
        CriticalPathAvailabilityEvaluator().evaluate(
            snapshot=build_snapshot(),
            policies=(
                build_policy(),
                build_policy(),
            ),
        )


def test_invalid_snapshot_is_rejected() -> None:
    with pytest.raises(
        TypeError,
        match="snapshot must be a MediaMTXSnapshot",
    ):
        CriticalPathAvailabilityEvaluator().evaluate(
            snapshot="invalid",  # type: ignore[arg-type]
            policies=(),
        )


def test_non_tuple_policies_are_rejected() -> None:
    with pytest.raises(
        TypeError,
        match="policies must be a tuple",
    ):
        CriticalPathAvailabilityEvaluator().evaluate(
            snapshot=build_snapshot(),
            policies=[],  # type: ignore[arg-type]
        )


def test_invalid_policy_member_is_rejected() -> None:
    with pytest.raises(
        TypeError,
        match=(
            "policies must contain only "
            "CriticalPathPolicy values"
        ),
    ):
        CriticalPathAvailabilityEvaluator().evaluate(
            snapshot=build_snapshot(),
            policies=(
                "invalid",  # type: ignore[arg-type]
            ),
        )


def test_available_evaluation_requires_media_path() -> None:
    with pytest.raises(
        ValueError,
        match="AVAILABLE evaluation requires a media_path",
    ):
        CriticalPathAvailabilityEvaluation(
            policy=build_policy(),
            state=CriticalPathAvailabilityState.AVAILABLE,
            media_path=None,
        )


def test_evaluation_rejects_invalid_policy() -> None:
    with pytest.raises(
        TypeError,
        match="policy must be a CriticalPathPolicy",
    ):
        CriticalPathAvailabilityEvaluation(
            policy="invalid",  # type: ignore[arg-type]
            state=CriticalPathAvailabilityState.UNAVAILABLE,
            media_path=None,
        )
