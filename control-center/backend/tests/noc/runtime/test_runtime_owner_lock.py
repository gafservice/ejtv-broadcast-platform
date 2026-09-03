"""Tests for process-safe NOC runtime ownership."""

from __future__ import annotations

from datetime import datetime, timezone
from multiprocessing import get_context
from pathlib import Path

from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.runtime.runtime_owner import RuntimeOwnershipError
from app.noc.runtime.runtime_owner_lock import RuntimeOwnerLock


def _node_id() -> NodeId:
    return NodeId(
        id="node-01",
        name="node-01",
        display_name="Node 01",
        created_at=datetime(
            2026,
            1,
            1,
            tzinfo=timezone.utc,
        ),
    )


def _try_acquire(
    root_path: str,
    result_queue,
) -> None:
    lock = RuntimeOwnerLock(root_path)

    try:
        with lock.exclusive(
            node_id=_node_id(),
            instance_id=NodeInstanceId("instance-01"),
        ):
            result_queue.put("acquired")
    except RuntimeOwnershipError:
        result_queue.put("denied")


def test_lock_path_is_deterministic_for_node_instance(
    tmp_path: Path,
) -> None:
    lock = RuntimeOwnerLock(tmp_path)

    first = lock.lock_path(
        node_id=_node_id(),
        instance_id=NodeInstanceId("instance-01"),
    )

    second = lock.lock_path(
        node_id=_node_id(),
        instance_id=NodeInstanceId("instance-01"),
    )

    assert first == second
    assert first.parent == tmp_path
    assert first.name.endswith(
        RuntimeOwnerLock.LOCK_SUFFIX
    )


def test_different_instances_use_different_lock_paths(
    tmp_path: Path,
) -> None:
    lock = RuntimeOwnerLock(tmp_path)

    primary = lock.lock_path(
        node_id=_node_id(),
        instance_id=NodeInstanceId("instance-01"),
    )

    backup = lock.lock_path(
        node_id=_node_id(),
        instance_id=NodeInstanceId("instance-02"),
    )

    assert primary != backup


def test_second_process_is_denied_while_owner_holds_lock(
    tmp_path: Path,
) -> None:
    lock = RuntimeOwnerLock(tmp_path)

    context = get_context("spawn")
    result_queue = context.Queue()

    with lock.exclusive(
        node_id=_node_id(),
        instance_id=NodeInstanceId("instance-01"),
    ):
        process = context.Process(
            target=_try_acquire,
            args=(
                str(tmp_path),
                result_queue,
            ),
        )

        process.start()
        process.join(timeout=10)

        assert process.exitcode == 0
        assert result_queue.get(timeout=2) == "denied"


def test_another_process_can_acquire_after_release(
    tmp_path: Path,
) -> None:
    lock = RuntimeOwnerLock(tmp_path)

    with lock.exclusive(
        node_id=_node_id(),
        instance_id=NodeInstanceId("instance-01"),
    ):
        pass

    context = get_context("spawn")
    result_queue = context.Queue()

    process = context.Process(
        target=_try_acquire,
        args=(
            str(tmp_path),
            result_queue,
        ),
    )

    process.start()
    process.join(timeout=10)

    assert process.exitcode == 0
    assert result_queue.get(timeout=2) == "acquired"
