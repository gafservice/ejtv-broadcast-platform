"""SQLite adapter for durable NOC historical range discovery.

ENG-013B — persistent operational history.
"""

from __future__ import annotations

from datetime import datetime

from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.history.sqlite_database import (
    SQLiteHistoryDatabase,
)


class SQLiteHistoricalRangeRepository:
    """Discover durable historical boundaries from SQLite history."""

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

    def first_historical_timestamp(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
    ) -> datetime | None:
        """Return the earliest Event or AlarmTransition timestamp."""

        if not isinstance(node_id, NodeId):
            raise TypeError(
                "node_id must be a NodeId"
            )

        if not isinstance(
            instance_id,
            NodeInstanceId,
        ):
            raise TypeError(
                "instance_id must be a NodeInstanceId"
            )

        with self._database.connect() as connection:
            row = connection.execute(
                """
                SELECT MIN(timestamp) AS first_timestamp
                FROM (
                    SELECT
                        MIN(event_timestamp) AS timestamp
                    FROM events
                    WHERE node_id = ?
                      AND instance_id = ?

                    UNION ALL

                    SELECT
                        MIN(t.transition_timestamp) AS timestamp
                    FROM alarm_transitions AS t
                    INNER JOIN alarms AS a
                        ON a.alarm_id = t.alarm_id
                    WHERE a.node_id = ?
                      AND a.instance_id = ?
                )
                """,
                (
                    node_id.id,
                    instance_id.value,
                    node_id.id,
                    instance_id.value,
                ),
            ).fetchone()

        if (
            row is None
            or row["first_timestamp"] is None
        ):
            return None

        return datetime.fromisoformat(
            row["first_timestamp"]
        )
