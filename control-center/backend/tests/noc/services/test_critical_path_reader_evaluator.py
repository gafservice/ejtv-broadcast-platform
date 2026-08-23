"""Tests for critical multimedia path reader evaluation."""

from datetime import UTC, datetime

import pytest

from app.domain.streaming.models import (
    MediaMTXSnapshot,
    MediaPath,
    MediaPathStatus,
    MediaReader,
    MediaSource,
)
from app.noc.domain.critical_path_policy import (
    CriticalPathPolicy,
)
from app.noc.services.critical_path_reader_evaluator import (
    CriticalPathReaderEvaluation,
    CriticalPathReaderEvaluator,
    CriticalPathReaderState,
)


TIMESTAMP = datetime(
    2026,
    8,
    23,
    3,
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
    reader_count: int = 0,
    ready: bool = True,
    available: bool = True,
    online: bool = True,
) -> MediaPath:
    if source is None and status is MediaPathStatus.ACTIVE:
        source = MediaSource(
            source_type="mpegtsSource",
        )

    readers = tuple(
        MediaReader(
            reader_type="srtConn",
            reader_id=f"reader-{index}",
        )
        for index in range(reader_count)
    )

    return MediaPath(
        name=name,
        configuration_name=name,
        status=status,
        ready=ready,
        available=available,
        online=online,
        source=source,
        readers=readers,
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
        CriticalPathReaderState.INACTIVE
    ) == "INACTIVE"

    assert str(
        CriticalPathReaderState.HAS_READERS
    ) == "HAS_READERS"

    assert str(
        CriticalPathReaderState.NO_READERS
    ) == "NO_READERS"


def test_missing_path_is_inactive() -> None:
    evaluator = CriticalPathReaderEvaluator()

    result = evaluator.evaluate(
        snapshot=build_snapshot(),
        policies=(build_policy(),),
    )

    assert len(result) == 1
    assert (
        result[0].state
        is CriticalPathReaderState.INACTIVE
    )
    assert result[0].media_path is None


def test_active_mpegts_path_with_readers_has_readers() -> None:
    evaluator = CriticalPathReaderEvaluator()

    path = build_path(
        reader_count=2,
    )

    result = evaluator.evaluate(
        snapshot=build_snapshot(path),
        policies=(build_policy(),),
    )

    assert (
        result[0].state
        is CriticalPathReaderState.HAS_READERS
    )
    assert result[0].media_path is path
    assert result[0].media_path.reader_count == 2
    assert (
        result[0].media_path.source.source_type
        == "mpegtsSource"
    )


def test_active_mpegts_path_without_readers_is_no_readers() -> None:
    evaluator = CriticalPathReaderEvaluator()

    path = build_path(
        reader_count=0,
    )

    result = evaluator.evaluate(
        snapshot=build_snapshot(path),
        policies=(build_policy(),),
    )

    assert (
        result[0].state
        is CriticalPathReaderState.NO_READERS
    )
    assert result[0].media_path is path
    assert result[0].media_path.reader_count == 0
    assert result[0].media_path.has_source is True


def test_no_source_path_is_inactive() -> None:
    evaluator = CriticalPathReaderEvaluator()

    path = build_path(
        status=MediaPathStatus.NO_SOURCE,
        source=None,
        reader_count=0,
        ready=False,
        available=False,
        online=False,
    )

    result = evaluator.evaluate(
        snapshot=build_snapshot(path),
        policies=(build_policy(),),
    )

    assert (
        result[0].state
        is CriticalPathReaderState.INACTIVE
    )
    assert result[0].media_path is path


def test_offline_path_is_inactive() -> None:
    evaluator = CriticalPathReaderEvaluator()

    path = build_path(
        status=MediaPathStatus.OFFLINE,
        source=MediaSource(
            source_type="mpegtsSource"
        ),
        reader_count=0,
        ready=False,
        available=False,
        online=False,
    )

    result = evaluator.evaluate(
        snapshot=build_snapshot(path),
        policies=(build_policy(),),
    )

    assert (
        result[0].state
        is CriticalPathReaderState.INACTIVE
    )


def test_path_without_source_is_inactive_even_if_status_active() -> None:
    evaluator = CriticalPathReaderEvaluator()

    path = MediaPath(
        name="ejtv",
        configuration_name="ejtv",
        status=MediaPathStatus.ACTIVE,
        ready=True,
        available=True,
        online=True,
        source=None,
        readers=(),
    )

    result = evaluator.evaluate(
        snapshot=build_snapshot(path),
        policies=(build_policy(),),
    )

    assert (
        result[0].state
        is CriticalPathReaderState.INACTIVE
    )


def test_other_paths_are_ignored() -> None:
    evaluator = CriticalPathReaderEvaluator()

    enlace = build_path(
        name="enlace",
        reader_count=1,
    )

    result = evaluator.evaluate(
        snapshot=build_snapshot(enlace),
        policies=(build_policy(path="ejtv"),),
    )

    assert (
        result[0].state
        is CriticalPathReaderState.INACTIVE
    )
    assert result[0].media_path is None


def test_disabled_policy_is_not_evaluated() -> None:
    evaluator = CriticalPathReaderEvaluator()

    result = evaluator.evaluate(
        snapshot=build_snapshot(
            build_path()
        ),
        policies=(
            build_policy(
                enabled=False,
            ),
        ),
    )

    assert result == ()


def test_multiple_policies_are_sorted_by_path() -> None:
    evaluator = CriticalPathReaderEvaluator()

    result = evaluator.evaluate(
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
    evaluator = CriticalPathReaderEvaluator()

    with pytest.raises(
        ValueError,
        match=(
            "policies must not contain duplicate "
            "path values"
        ),
    ):
        evaluator.evaluate(
            snapshot=build_snapshot(),
            policies=(
                build_policy(path="ejtv"),
                build_policy(path="ejtv"),
            ),
        )


def test_invalid_snapshot_is_rejected() -> None:
    evaluator = CriticalPathReaderEvaluator()

    with pytest.raises(
        TypeError,
        match="snapshot must be a MediaMTXSnapshot",
    ):
        evaluator.evaluate(
            snapshot="invalid",  # type: ignore[arg-type]
            policies=(),
        )


def test_non_tuple_policies_are_rejected() -> None:
    evaluator = CriticalPathReaderEvaluator()

    with pytest.raises(
        TypeError,
        match="policies must be a tuple",
    ):
        evaluator.evaluate(
            snapshot=build_snapshot(),
            policies=[],  # type: ignore[arg-type]
        )


def test_invalid_policy_member_is_rejected() -> None:
    evaluator = CriticalPathReaderEvaluator()

    with pytest.raises(
        TypeError,
        match=(
            "policies must contain only "
            "CriticalPathPolicy values"
        ),
    ):
        evaluator.evaluate(
            snapshot=build_snapshot(),
            policies=(
                "invalid",  # type: ignore[arg-type]
            ),
        )


def test_evaluation_rejects_invalid_policy() -> None:
    with pytest.raises(
        TypeError,
        match="policy must be a CriticalPathPolicy",
    ):
        CriticalPathReaderEvaluation(
            policy="invalid",  # type: ignore[arg-type]
            state=CriticalPathReaderState.INACTIVE,
            media_path=None,
        )


def test_evaluation_rejects_invalid_media_path() -> None:
    with pytest.raises(
        TypeError,
        match="media_path must be a MediaPath or None",
    ):
        CriticalPathReaderEvaluation(
            policy=build_policy(),
            state=CriticalPathReaderState.INACTIVE,
            media_path="invalid",  # type: ignore[arg-type]
        )


def test_has_readers_requires_media_path() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "active critical-path evaluation requires "
            "a media_path"
        ),
    ):
        CriticalPathReaderEvaluation(
            policy=build_policy(),
            state=CriticalPathReaderState.HAS_READERS,
            media_path=None,
        )


def test_has_readers_requires_at_least_one_reader() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "HAS_READERS evaluation requires "
            "at least one reader"
        ),
    ):
        CriticalPathReaderEvaluation(
            policy=build_policy(),
            state=CriticalPathReaderState.HAS_READERS,
            media_path=build_path(
                reader_count=0,
            ),
        )


def test_no_readers_requires_zero_readers() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "NO_READERS evaluation requires "
            "zero readers"
        ),
    ):
        CriticalPathReaderEvaluation(
            policy=build_policy(),
            state=CriticalPathReaderState.NO_READERS,
            media_path=build_path(
                reader_count=1,
            ),
        )
