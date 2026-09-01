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

        mature_day = (
            effective_through.astimezone(
                timezone.utc
            ).date()
            - timedelta(days=2)
        )

        self._evidence_day_sealer.seal_day(
            mature_day
        )

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
