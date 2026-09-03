"""Process-safe exclusive ownership for one NOC NodeInstance.

ENG-013B — Node SDK.

Only one operating-system process may own the operational runtime for a
given NodeId / NodeInstanceId pair at a time.

The lock is advisory and process-safe on POSIX systems.  The lock file is
persistent, but ownership exists only while ``flock`` is held by an open
file descriptor.
"""

from __future__ import annotations

import fcntl
import hashlib
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, TextIO

from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.runtime.runtime_owner import RuntimeOwnershipError


class RuntimeOwnerLock:
    """Provide non-blocking inter-process ownership of one NodeInstance."""

    LOCK_SUFFIX = ".runtime-owner.lock"

    def __init__(
        self,
        root_path: str | Path,
    ) -> None:
        self._root_path = Path(root_path)

    @property
    def root_path(self) -> Path:
        return self._root_path

    def lock_path(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
    ) -> Path:
        """Return the deterministic lock path for one NodeInstance."""

        identity = (
            f"{node_id.id}\0{instance_id.value}"
        ).encode("utf-8")

        digest = hashlib.sha256(identity).hexdigest()

        return (
            self._root_path
            / f"{digest}{self.LOCK_SUFFIX}"
        )

    @contextmanager
    def exclusive(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
    ) -> Iterator[Path]:
        """Acquire exclusive ownership without waiting.

        Raises RuntimeOwnershipError immediately when another process
        already owns the same NodeInstance.
        """

        self._root_path.mkdir(
            parents=True,
            exist_ok=True,
        )

        lock_path = self.lock_path(
            node_id=node_id,
            instance_id=instance_id,
        )

        handle: TextIO

        with lock_path.open(
            "a+",
            encoding="utf-8",
        ) as handle:
            try:
                fcntl.flock(
                    handle.fileno(),
                    fcntl.LOCK_EX | fcntl.LOCK_NB,
                )
            except BlockingIOError as exc:
                raise RuntimeOwnershipError(
                    "Operational runtime ownership is already held "
                    f"for node={node_id.id!r}, "
                    f"instance={instance_id.value!r}"
                ) from exc

            try:
                yield lock_path
            finally:
                fcntl.flock(
                    handle.fileno(),
                    fcntl.LOCK_UN,
                )
