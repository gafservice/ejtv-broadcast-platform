"""Runtime periódico para mantenimiento histórico diario del NOC."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, time, timedelta, timezone
from typing import Callable

from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.history.evidence_day_sealer import (
    EvidenceDaySealer,
)
from app.noc.history.historical_range_repository import (
    HistoricalRangeRepository,
)
from app.noc.services.daily_alarm_continuity_service import (
    DailyAlarmContinuityService,
)
from app.noc.services.evidence_reconciliation_service import (
    EvidenceReconciliationService,
)


logger = logging.getLogger(__name__)


class DailyHistoryMaintenanceRuntime:
    """Ejecuta continuidad y reconciliación en fronteras diarias UTC."""

    def __init__(
        self,
        *,
        continuity_service: DailyAlarmContinuityService,
        reconciliation_service: EvidenceReconciliationService,
        evidence_day_sealer: EvidenceDaySealer,
        historical_range_repository: HistoricalRangeRepository | None = None,
        clock: Callable[[], datetime] | None = None,
        retry_delay_seconds: float = 60.0,
    ) -> None:
        if not isinstance(
            continuity_service,
            DailyAlarmContinuityService,
        ):
            raise TypeError(
                "continuity_service must be a "
                "DailyAlarmContinuityService"
            )

        if not isinstance(
            reconciliation_service,
            EvidenceReconciliationService,
        ):
            raise TypeError(
                "reconciliation_service must be an "
                "EvidenceReconciliationService"
            )

        if not isinstance(
            evidence_day_sealer,
            EvidenceDaySealer,
        ):
            raise TypeError(
                "evidence_day_sealer must be an "
                "EvidenceDaySealer"
            )

        if (
            historical_range_repository is not None
            and not isinstance(
                historical_range_repository,
                HistoricalRangeRepository,
            )
        ):
            raise TypeError(
                "historical_range_repository must satisfy "
                "HistoricalRangeRepository"
            )

        if (
            not isinstance(
                retry_delay_seconds,
                (int, float),
            )
            or isinstance(
                retry_delay_seconds,
                bool,
            )
        ):
            raise TypeError(
                "retry_delay_seconds must be a number"
            )

        if retry_delay_seconds <= 0:
            raise ValueError(
                "retry_delay_seconds must be greater than zero"
            )

        self._continuity_service = continuity_service
        self._reconciliation_service = reconciliation_service
        self._evidence_day_sealer = evidence_day_sealer
        self._historical_range_repository = historical_range_repository
        self._clock = clock or (
            lambda: datetime.now(timezone.utc)
        )
        self._retry_delay_seconds = float(
            retry_delay_seconds
        )

    @staticmethod
    def next_utc_boundary(
        now: datetime,
    ) -> datetime:
        if not isinstance(now, datetime):
            raise TypeError("now must be a datetime")

        if (
            now.tzinfo is None
            or now.utcoffset() is None
        ):
            raise ValueError(
                "now must be timezone-aware"
            )

        now_utc = now.astimezone(timezone.utc)

        return datetime.combine(
            now_utc.date() + timedelta(days=1),
            time.min,
            tzinfo=timezone.utc,
        )

    def run_once(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        through: datetime | None = None,
    ) -> None:
        effective_through = (
            self._clock()
            if through is None
            else through
        )

        self._continuity_service.catch_up(
            node_id=node_id,
            instance_id=instance_id,
            through=effective_through,
        )

        reconciliation_end = (
            effective_through
            + timedelta(microseconds=1)
        )

        self._reconciliation_service.reconcile_between(
            start=effective_through - timedelta(hours=48),
            end=reconciliation_end,
            node_id=node_id,
            instance_id=instance_id,
        )

        self.catch_up_mature_days(
            node_id=node_id,
            instance_id=instance_id,
            through=effective_through,
        )

    def catch_up_mature_days(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        through: datetime,
    ) -> None:
        """Reconcile and seal every pending mature UTC day."""

        if not isinstance(through, datetime):
            raise TypeError(
                "through must be a datetime"
            )

        if (
            through.tzinfo is None
            or through.utcoffset() is None
        ):
            raise ValueError(
                "through must be timezone-aware"
            )

        mature_day = (
            through.astimezone(
                timezone.utc
            ).date()
            - timedelta(days=2)
        )

        if self._historical_range_repository is None:
            mature_day_start = datetime.combine(
                mature_day,
                time.min,
                tzinfo=timezone.utc,
            )

            mature_day_end = (
                mature_day_start
                + timedelta(days=1)
            )

            self._reconciliation_service.reconcile_between(
                start=mature_day_start,
                end=mature_day_end,
                node_id=node_id,
                instance_id=instance_id,
            )

            self._evidence_day_sealer.seal_day(
                mature_day
            )

            return

        first_timestamp = (
            self._historical_range_repository
            .first_historical_timestamp(
                node_id=node_id,
                instance_id=instance_id,
            )
        )

        if first_timestamp is None:
            return

        first_day = first_timestamp.astimezone(
            timezone.utc
        ).date()

        if first_day > mature_day:
            return

        day = first_day

        while day <= mature_day:
            if self._evidence_day_sealer.verify_day(
                day
            ):
                day += timedelta(days=1)
                continue

            self._evidence_day_sealer.assert_day_can_be_finalized(
                day
            )

            day_start = datetime.combine(
                day,
                time.min,
                tzinfo=timezone.utc,
            )

            day_end = (
                day_start
                + timedelta(days=1)
            )

            self._reconciliation_service.reconcile_between(
                start=day_start,
                end=day_end,
                node_id=node_id,
                instance_id=instance_id,
            )

            self._evidence_day_sealer.seal_day(
                day
            )

            day += timedelta(days=1)

    async def run_forever(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
    ) -> None:
        while True:
            now = self._clock()

            boundary = self.next_utc_boundary(
                now
            )

            delay = max(
                0.0,
                (boundary - now.astimezone(
                    timezone.utc
                )).total_seconds(),
            )

            await asyncio.sleep(delay)

            while True:
                try:
                    self.run_once(
                        node_id=node_id,
                        instance_id=instance_id,
                        through=boundary,
                    )
                except Exception:
                    logger.exception(
                        "Daily NOC history maintenance "
                        "failed at UTC boundary %s; "
                        "retrying in %.1f seconds",
                        boundary.isoformat(),
                        self._retry_delay_seconds,
                    )

                    await asyncio.sleep(
                        self._retry_delay_seconds
                    )

                    continue

                break
