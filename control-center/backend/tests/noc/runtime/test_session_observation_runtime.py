"""Tests for the multimedia session observation runtime."""

from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import pytest

from app.adapters.mediamtx.adapter import MediaMTXAdapter
from app.adapters.mediamtx.session_adapter import MediaMTXSessionAdapter
from app.domain.sessions import SessionSnapshot
from app.domain.streaming.models import MediaMTXSnapshot
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.runtime.session_observation_runtime import (
    SessionObservationRuntime,
    SessionObservationResult,
)
from app.noc.runtime.session_operational_runtime import (
    SessionOperationalRuntime,
)
from app.services.streaming_service import StreamingService


TIMESTAMP = datetime(
    2026,
    9,
    3,
    5,
    0,
    tzinfo=UTC,
)

NODE_ID = NodeId.create(
    id="streaming-core",
    name="streaming",
    display_name="Streaming Core",
)

INSTANCE_ID = NodeInstanceId("streaming-primary")


def media_snapshot(
    *,
    captured_at: datetime = TIMESTAMP,
) -> MediaMTXSnapshot:
    return MediaMTXSnapshot(
        captured_at=captured_at,
        paths=(),
        reported_item_count=0,
        reported_page_count=0,
    )


def session_snapshot(
    *,
    captured_at: datetime = TIMESTAMP,
) -> SessionSnapshot:
    return SessionSnapshot(
        captured_at=captured_at,
        sessions=(),
    )


def build_runtime(
    *,
    media_snapshots: tuple[MediaMTXSnapshot, ...],
    session_snapshots: tuple[SessionSnapshot, ...],
):
    mediamtx_adapter = object.__new__(MediaMTXAdapter)
    mediamtx_adapter.get_snapshot = Mock(
        side_effect=media_snapshots
    )

    session_adapter = object.__new__(
        MediaMTXSessionAdapter
    )
    session_adapter.get_snapshot = Mock(
        side_effect=session_snapshots
    )

    streaming_service = StreamingService()

    operational_runtime = object.__new__(
        SessionOperationalRuntime
    )
    operational_runtime.process = Mock(
        return_value=Mock()
    )

    runtime = SessionObservationRuntime(
        mediamtx_adapter=mediamtx_adapter,
        session_adapter=session_adapter,
        streaming_service=streaming_service,
        operational_runtime=operational_runtime,
    )

    return (
        runtime,
        mediamtx_adapter,
        session_adapter,
        operational_runtime,
    )


def test_first_cycle_uses_empty_temporal_baseline() -> None:
    media = media_snapshot()
    sessions = session_snapshot()

    (
        runtime,
        mediamtx_adapter,
        session_adapter,
        operational_runtime,
    ) = build_runtime(
        media_snapshots=(media,),
        session_snapshots=(sessions,),
    )

    result = runtime.run_once(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
    )

    assert isinstance(result, SessionObservationResult)

    mediamtx_adapter.get_snapshot.assert_called_once_with()
    session_adapter.get_snapshot.assert_called_once_with()

    assert result.media_snapshot is media
    assert result.session_snapshot is sessions

    assert result.streaming_measurement.previous_captured_at is None

    operational_runtime.process.assert_called_once_with(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        previous=None,
        current=sessions,
        media_snapshot=media,
        streaming_measurement=result.streaming_measurement,
        timestamp=sessions.captured_at,
    )


def test_second_cycle_uses_first_cycle_as_previous_state() -> None:
    first_time = TIMESTAMP
    second_time = TIMESTAMP + timedelta(seconds=5)

    first_media = media_snapshot(
        captured_at=first_time
    )
    second_media = media_snapshot(
        captured_at=second_time
    )

    first_sessions = session_snapshot(
        captured_at=first_time
    )
    second_sessions = session_snapshot(
        captured_at=second_time
    )

    (
        runtime,
        _,
        _,
        operational_runtime,
    ) = build_runtime(
        media_snapshots=(
            first_media,
            second_media,
        ),
        session_snapshots=(
            first_sessions,
            second_sessions,
        ),
    )

    first_result = runtime.run_once(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
    )

    second_result = runtime.run_once(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
    )

    assert first_result.streaming_measurement.previous_captured_at is None

    assert (
        second_result.streaming_measurement.previous_captured_at
        == first_media.captured_at
    )
    assert second_result.streaming_measurement.interval_seconds == 5.0

    assert operational_runtime.process.call_count == 2

    second_call = operational_runtime.process.call_args_list[1]

    assert second_call.kwargs["previous"] is first_sessions
    assert second_call.kwargs["current"] is second_sessions
    assert second_call.kwargs["media_snapshot"] is second_media


def test_failed_operational_cycle_does_not_advance_previous_state() -> None:
    first_time = TIMESTAMP
    failed_time = TIMESTAMP + timedelta(seconds=5)
    retry_time = TIMESTAMP + timedelta(seconds=10)

    first_media = media_snapshot(
        captured_at=first_time
    )
    failed_media = media_snapshot(
        captured_at=failed_time
    )
    retry_media = media_snapshot(
        captured_at=retry_time
    )

    first_sessions = session_snapshot(
        captured_at=first_time
    )
    failed_sessions = session_snapshot(
        captured_at=failed_time
    )
    retry_sessions = session_snapshot(
        captured_at=retry_time
    )

    (
        runtime,
        _,
        _,
        operational_runtime,
    ) = build_runtime(
        media_snapshots=(
            first_media,
            failed_media,
            retry_media,
        ),
        session_snapshots=(
            first_sessions,
            failed_sessions,
            retry_sessions,
        ),
    )

    runtime.run_once(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
    )

    operational_runtime.process.side_effect = [
        RuntimeError("operational failure"),
        Mock(),
    ]

    with pytest.raises(
        RuntimeError,
        match="operational failure",
    ):
        runtime.run_once(
            node_id=NODE_ID,
            instance_id=INSTANCE_ID,
        )

    result = runtime.run_once(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
    )

    retry_call = operational_runtime.process.call_args_list[2]

    assert retry_call.kwargs["previous"] is first_sessions

    assert (
        result.streaming_measurement.previous_captured_at
        == first_media.captured_at
    )

    assert result.streaming_measurement.interval_seconds == 10.0


def test_run_forever_rejects_non_positive_interval() -> None:
    import asyncio

    (
        runtime,
        _,
        _,
        _,
    ) = build_runtime(
        media_snapshots=(),
        session_snapshots=(),
    )

    with pytest.raises(
        ValueError,
        match="interval_seconds must be greater than zero",
    ):
        asyncio.run(
            runtime.run_forever(
                node_id=NODE_ID,
                instance_id=INSTANCE_ID,
                interval_seconds=0,
            )
        )
