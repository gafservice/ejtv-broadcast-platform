"""Bootstrap of durable managed-history authority.

ENG-013B — persistent operational history.

This service establishes the immutable UTC-day lower bound for managed
history of one NodeInstance.

Existing installations bootstrap from the earliest observable durable
historical timestamp. New installations bootstrap from the current UTC
day when runtime ownership begins.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Callable

from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.history.historical_range_repository import (
    HistoricalRangeRepository,
)
from app.noc.history.managed_history_repository import (
    ManagedHistoryRepository,
)


class ManagedHistoryBootstrapService:
    """Establish the immutable managed-history anchor once."""

    def __init__(
        self,
        *,
        managed_history_repository: ManagedHistoryRepository,
        historical_range_repository: HistoricalRangeRepository,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if not isinstance(
            managed_history_repository,
            ManagedHistoryRepository,
        ):
            raise TypeError(
                "managed_history_repository must satisfy "
                "ManagedHistoryRepository"
            )

        if not isinstance(
            historical_range_repository,
            HistoricalRangeRepository,
        ):
            raise TypeError(
                "historical_range_repository must satisfy "
                "HistoricalRangeRepository"
            )

        self._managed_history_repository = (
            managed_history_repository
        )
        self._historical_range_repository = (
            historical_range_repository
        )
        self._clock = clock or (
            lambda: datetime.now(timezone.utc)
        )

    def ensure_anchor(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
    ) -> date:
        """Return the existing anchor or establish it exactly once."""

        existing = (
            self._managed_history_repository
            .get_managed_since_day(
                node_id=node_id,
                instance_id=instance_id,
            )
        )

        if existing is not None:
            return existing

        now = self._clock()

        if not isinstance(now, datetime):
            raise TypeError(
                "clock must return a datetime"
            )

        if (
            now.tzinfo is None
            or now.utcoffset() is None
        ):
            raise ValueError(
                "clock must return a timezone-aware datetime"
            )

        now_utc = now.astimezone(
            timezone.utc
        )

        first_timestamp = (
            self._historical_range_repository
            .first_historical_timestamp(
                node_id=node_id,
                instance_id=instance_id,
            )
        )

        if first_timestamp is None:
            managed_day = now_utc.date()
        else:
            if not isinstance(
                first_timestamp,
                datetime,
            ):
                raise TypeError(
                    "first historical timestamp must be a datetime"
                )

            if (
                first_timestamp.tzinfo is None
                or first_timestamp.utcoffset() is None
            ):
                raise ValueError(
                    "first historical timestamp must be "
                    "timezone-aware"
                )

            managed_day = (
                first_timestamp.astimezone(
                    timezone.utc
                ).date()
            )

        return (
            self._managed_history_repository
            .ensure_managed_since_day(
                node_id=node_id,
                instance_id=instance_id,
                day=managed_day,
                created_at=now_utc,
            )
        )
