"""SQLite repository for stabilized Media Health current state.

ENG-013C — Media Health Current State

This adapter stores the latest known stabilized MediaHealth value for
each profile/service/path identity in the shared NOC SQLite database.

It is a current-state projection, not immutable operational history.
"""

from __future__ import annotations

from app.noc.current_state.media_health_codec import (
    MediaHealthCodec,
)
from app.noc.current_state.media_health_current_state import (
    MediaHealthCurrentState,
    MediaHealthCurrentStateRepository,
)
from app.noc.history.sqlite_database import (
    SQLiteHistoryDatabase,
)


class SQLiteMediaHealthCurrentStateRepository(
    MediaHealthCurrentStateRepository
):
    """Persist latest stabilized Media Health state in SQLite."""

    def __init__(
        self,
        database: SQLiteHistoryDatabase,
    ) -> None:
        if not isinstance(
            database,
            SQLiteHistoryDatabase,
        ):
            raise TypeError(
                "database must be a SQLiteHistoryDatabase"
            )

        self._database = database
        self._database.initialize()

    def save(
        self,
        *,
        state: MediaHealthCurrentState,
    ) -> None:
        if not isinstance(
            state,
            MediaHealthCurrentState,
        ):
            raise TypeError(
                "state must be a MediaHealthCurrentState"
            )

        observed_at = state.observed_at.isoformat(
            timespec="microseconds"
        )

        payload = MediaHealthCodec.encode(
            state.health
        )

        with self._database.connect() as connection:
            connection.execute(
                """
                INSERT INTO media_health_current_state (
                    profile_id,
                    service_id,
                    path_name,
                    observed_at,
                    health_json
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(
                    profile_id,
                    service_id,
                    path_name
                )
                DO UPDATE SET
                    observed_at = excluded.observed_at,
                    health_json = excluded.health_json
                WHERE
                    excluded.observed_at
                    >= media_health_current_state.observed_at
                """,
                (
                    state.profile_id,
                    state.service_id,
                    state.path_name,
                    observed_at,
                    payload,
                ),
            )

    def latest(
        self,
        *,
        profile_id: str,
        service_id: str,
        path_name: str,
    ) -> MediaHealthCurrentState | None:
        profile_id = self._normalize_identity(
            profile_id,
            "profile_id",
        )
        service_id = self._normalize_identity(
            service_id,
            "service_id",
        )
        path_name = self._normalize_identity(
            path_name,
            "path_name",
        )

        with self._database.connect() as connection:
            row = connection.execute(
                """
                SELECT
                    observed_at,
                    health_json
                FROM media_health_current_state
                WHERE profile_id = ?
                  AND service_id = ?
                  AND path_name = ?
                """,
                (
                    profile_id,
                    service_id,
                    path_name,
                ),
            ).fetchone()

        if row is None:
            return None

        health = MediaHealthCodec.decode(
            row["health_json"]
        )

        return MediaHealthCurrentState(
            profile_id=profile_id,
            service_id=service_id,
            path_name=path_name,
            observed_at=self._decode_datetime(
                row["observed_at"]
            ),
            health=health,
        )

    @staticmethod
    def _normalize_identity(
        value: str,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise TypeError(
                f"{field_name} must be a string"
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                f"{field_name} must not be blank"
            )

        return normalized

    @staticmethod
    def _decode_datetime(
        value: object,
    ):
        from datetime import datetime

        if not isinstance(value, str):
            raise ValueError(
                "observed_at must be a string"
            )

        return datetime.fromisoformat(value)
