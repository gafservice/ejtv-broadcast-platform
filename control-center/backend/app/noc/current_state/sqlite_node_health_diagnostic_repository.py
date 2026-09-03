"""SQLite repository for shared NodeHealthDiagnostic current state.

ENG-013B — Current State

This adapter stores the latest known Node health diagnostic for each
NodeInstance in the shared NOC SQLite database.

It is a current-state projection, not immutable operational history.
"""

from __future__ import annotations

from app.noc.current_state.node_health_diagnostic_codec import (
    NodeHealthDiagnosticCodec,
)
from app.noc.current_state.repository import (
    NodeHealthDiagnosticRepository,
)
from app.noc.domain.node_health_diagnostic import (
    NodeHealthDiagnostic,
)
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.history.sqlite_database import (
    SQLiteHistoryDatabase,
)


class SQLiteNodeHealthDiagnosticRepository(
    NodeHealthDiagnosticRepository
):
    """Persist latest NodeHealthDiagnostic values in SQLite."""

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
        node_id: NodeId,
        instance_id: NodeInstanceId,
        diagnostic: NodeHealthDiagnostic,
    ) -> None:
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

        if not isinstance(
            diagnostic,
            NodeHealthDiagnostic,
        ):
            raise TypeError(
                "diagnostic must be a NodeHealthDiagnostic"
            )

        captured_at = diagnostic.captured_at.isoformat(
            timespec="microseconds"
        )

        payload = NodeHealthDiagnosticCodec.encode(
            diagnostic
        )

        with self._database.connect() as connection:
            connection.execute(
                """
                INSERT INTO node_health_diagnostics (
                    node_id,
                    instance_id,
                    captured_at,
                    diagnostic_json
                )
                VALUES (?, ?, ?, ?)
                ON CONFLICT(node_id, instance_id)
                DO UPDATE SET
                    captured_at = excluded.captured_at,
                    diagnostic_json = excluded.diagnostic_json
                WHERE
                    excluded.captured_at
                    >= node_health_diagnostics.captured_at
                """,
                (
                    node_id.id,
                    instance_id.value,
                    captured_at,
                    payload,
                ),
            )

    def latest(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
    ) -> NodeHealthDiagnostic | None:
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
                SELECT diagnostic_json
                FROM node_health_diagnostics
                WHERE node_id = ?
                  AND instance_id = ?
                """,
                (
                    node_id.id,
                    instance_id.value,
                ),
            ).fetchone()

        if row is None:
            return None

        return NodeHealthDiagnosticCodec.decode(
            row["diagnostic_json"]
        )
