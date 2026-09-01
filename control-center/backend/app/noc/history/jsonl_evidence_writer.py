"""Filesystem JSONL writer for NOC operational evidence.

ENG-013B — persistent operational history.

Records are written append-only into UTC daily directories.  Exact retries
are idempotent: an evidence identifier already present with the same
canonical payload is accepted without appending a duplicate line.
Conflicting reuse of an identifier is rejected.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from threading import RLock

from app.noc.history.alarm_transition import AlarmTransition
from app.noc.history.daily_evidence_lock import (
    DailyEvidenceLock,
)
from app.noc.history.evidence_writer import (
    EvidenceWriter,
    serialize_alarm_transition_evidence,
    serialize_event_evidence,
)
from app.noc.history.event_history_record import EventHistoryRecord


class EvidenceConflictError(ValueError):
    """Raised when an evidence identifier is reused with different data."""


class EvidenceDaySealedError(RuntimeError):
    """Raised when evidence is appended to a sealed UTC day."""


class JsonlEvidenceWriter(EvidenceWriter):
    """Append operational evidence to UTC daily JSONL files."""

    MANIFEST_FILENAME = "manifest.sha256"

    def __init__(self, root_path: str | Path) -> None:
        self._root_path = Path(root_path)
        self._lock = RLock()
        self._daily_lock = DailyEvidenceLock(
            self._root_path
        )

    @property
    def root_path(self) -> Path:
        return self._root_path

    def append_event(
        self,
        record: EventHistoryRecord,
    ) -> None:
        """Append one EventHistoryRecord idempotently."""

        path = self._daily_path(
            timestamp=record.recorded_at,
            filename="events.jsonl",
        )

        self._append_idempotent(
            day=record.recorded_at.date(),
            path=path,
            encoded=serialize_event_evidence(record),
            identity_field="event_id",
            identity=record.event_id,
        )

    def append_alarm_transition(
        self,
        transition: AlarmTransition,
    ) -> None:
        """Append one AlarmTransition idempotently."""

        path = self._daily_path(
            timestamp=transition.timestamp,
            filename="alarm_transitions.jsonl",
        )

        self._append_idempotent(
            day=transition.timestamp.date(),
            path=path,
            encoded=serialize_alarm_transition_evidence(
                transition
            ),
            identity_field="transition_id",
            identity=transition.transition_id,
        )

    def _daily_path(
        self,
        *,
        timestamp,
        filename: str,
    ) -> Path:
        """Resolve one UTC daily evidence file path."""

        return (
            self._root_path
            / f"{timestamp.year:04d}"
            / f"{timestamp.month:02d}"
            / f"{timestamp.day:02d}"
            / filename
        )

    def _append_idempotent(
        self,
        *,
        day,
        path: Path,
        encoded: str,
        identity_field: str,
        identity: str,
    ) -> None:
        """Append one canonical line with day-wide process safety."""

        with self._lock:
            with self._daily_lock.exclusive(
                day
            ) as directory:
                manifest_path = (
                    directory
                    / self.MANIFEST_FILENAME
                )

                if manifest_path.exists():
                    raise EvidenceDaySealedError(
                        "evidence day is sealed: "
                        f"{directory}"
                    )

                with path.open(
                    "a+",
                    encoding="utf-8",
                    newline="\n",
                ) as handle:
                    handle.seek(0)

                    for raw_line in handle:
                        line = raw_line.rstrip(
                            "\r\n"
                        )

                        if not line:
                            continue

                        try:
                            payload = json.loads(
                                line
                            )
                        except json.JSONDecodeError as exc:
                            raise EvidenceConflictError(
                                "invalid JSONL evidence "
                                f"in {path}"
                            ) from exc

                        if payload.get(
                            identity_field
                        ) != identity:
                            continue

                        if line == encoded:
                            return

                        raise EvidenceConflictError(
                            f"evidence identity "
                            f"{identity!r} already "
                            "exists with conflicting "
                            "payload"
                        )

                    handle.seek(
                        0,
                        os.SEEK_END,
                    )
                    handle.write(encoded)
                    handle.write("\n")
                    handle.flush()
                    os.fsync(handle.fileno())
