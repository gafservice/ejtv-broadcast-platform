"""SQLite repository for canonical Signal Health current state."""

from __future__ import annotations

from datetime import datetime

from app.noc.current_state.signal_health_codec import SignalHealthCodec
from app.noc.current_state.signal_health_current_state import (
    SignalHealthCurrentState,
    SignalHealthCurrentStateRepository,
)
from app.noc.history.sqlite_database import SQLiteHistoryDatabase


class SQLiteSignalHealthCurrentStateRepository(
    SignalHealthCurrentStateRepository,
):
    """Persist the latest canonical Signal Health per path identity."""

    def __init__(
        self,
        database: SQLiteHistoryDatabase,
    ) -> None:
        if not isinstance(database, SQLiteHistoryDatabase):
            raise TypeError(
                "database must be a SQLiteHistoryDatabase"
            )

        self._database = database
        self._codec = SignalHealthCodec()

    def save(
        self,
        *,
        state: SignalHealthCurrentState,
    ) -> None:
        if not isinstance(state, SignalHealthCurrentState):
            raise TypeError(
                "state must be a SignalHealthCurrentState"
            )

        with self._database.connect() as connection:
            connection.execute(
                """
                INSERT INTO signal_health_current_state (
                    profile_id,
                    service_id,
                    path_name,
                    observed_at,
                    health_since,
                    health_json
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT (
                    profile_id,
                    service_id,
                    path_name
                )
                DO UPDATE SET
                    observed_at = excluded.observed_at,
                    health_since = excluded.health_since,
                    health_json = excluded.health_json
                WHERE excluded.observed_at >=
                      signal_health_current_state.observed_at
                """,
                (
                    state.profile_id,
                    state.service_id,
                    state.path_name,
                    state.observed_at.isoformat(),
                    state.health_since.isoformat(),
                    self._codec.encode(state.health),
                ),
            )
            connection.commit()

    def latest(
        self,
        *,
        profile_id: str,
        service_id: str,
        path_name: str,
    ) -> SignalHealthCurrentState | None:
        normalized_profile_id = self._normalize_identity(
            profile_id,
            field_name="profile_id",
        )
        normalized_service_id = self._normalize_identity(
            service_id,
            field_name="service_id",
        )
        normalized_path_name = self._normalize_identity(
            path_name,
            field_name="path_name",
        )

        with self._database.connect() as connection:
            row = connection.execute(
                """
                SELECT
                    observed_at,
                    health_since,
                    health_json
                FROM signal_health_current_state
                WHERE profile_id = ?
                  AND service_id = ?
                  AND path_name = ?
                """,
                (
                    normalized_profile_id,
                    normalized_service_id,
                    normalized_path_name,
                ),
            ).fetchone()

        if row is None:
            return None

        if row["health_since"] is None:
            return None

        return SignalHealthCurrentState(
            profile_id=normalized_profile_id,
            service_id=normalized_service_id,
            path_name=normalized_path_name,
            observed_at=datetime.fromisoformat(
                row["observed_at"]
            ),
            health_since=datetime.fromisoformat(
                row["health_since"]
            ),
            health=self._codec.decode(
                row["health_json"]
            ),
        )

    @staticmethod
    def _normalize_identity(
        value: str,
        *,
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
