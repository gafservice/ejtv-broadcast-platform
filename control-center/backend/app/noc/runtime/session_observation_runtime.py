"""Periodic observation runtime for multimedia sessions.

ENG-013B — Node SDK

SessionObservationRuntime owns the temporal observation state required
to feed SessionOperationalRuntime.

It captures MediaMTX and session snapshots, derives streaming
measurements from consecutive media snapshots, and delegates all
session transition/event/alarm decisions to SessionOperationalRuntime.

It does not render dashboards and does not own persistence.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from app.adapters.mediamtx.adapter import MediaMTXAdapter
from app.adapters.mediamtx.session_adapter import MediaMTXSessionAdapter
from app.domain.sessions import SessionSnapshot
from app.domain.streaming import MediaMTXSnapshot
from app.domain.streaming.metrics import StreamingMeasurement
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.runtime.session_operational_runtime import (
    SessionOperationalRuntime,
    SessionOperationalRuntimeResult,
)
from app.services.streaming_service import StreamingService


@dataclass(frozen=True, slots=True)
class SessionObservationResult:
    """Result of one multimedia observation cycle."""

    media_snapshot: MediaMTXSnapshot
    session_snapshot: SessionSnapshot
    streaming_measurement: StreamingMeasurement
    operational_result: SessionOperationalRuntimeResult


class SessionObservationRuntime:
    """Capture multimedia state and feed the operational session runtime."""

    def __init__(
        self,
        *,
        mediamtx_adapter: MediaMTXAdapter,
        session_adapter: MediaMTXSessionAdapter,
        streaming_service: StreamingService,
        operational_runtime: SessionOperationalRuntime,
    ) -> None:
        if not isinstance(mediamtx_adapter, MediaMTXAdapter):
            raise TypeError(
                "mediamtx_adapter must be a MediaMTXAdapter"
            )

        if not isinstance(
            session_adapter,
            MediaMTXSessionAdapter,
        ):
            raise TypeError(
                "session_adapter must be a MediaMTXSessionAdapter"
            )

        if not isinstance(streaming_service, StreamingService):
            raise TypeError(
                "streaming_service must be a StreamingService"
            )

        if not isinstance(
            operational_runtime,
            SessionOperationalRuntime,
        ):
            raise TypeError(
                "operational_runtime must be a "
                "SessionOperationalRuntime"
            )

        self._mediamtx_adapter = mediamtx_adapter
        self._session_adapter = session_adapter
        self._streaming_service = streaming_service
        self._operational_runtime = operational_runtime

        self._previous_media_snapshot: MediaMTXSnapshot | None = None
        self._previous_session_snapshot: SessionSnapshot | None = None

    def run_once(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
    ) -> SessionObservationResult:
        """Execute one operational multimedia observation cycle."""

        media_snapshot = self._mediamtx_adapter.get_snapshot()
        session_snapshot = self._session_adapter.get_snapshot()

        streaming_measurement = self._streaming_service.compare(
            self._previous_media_snapshot,
            media_snapshot,
        )

        operational_result = self._operational_runtime.process(
            node_id=node_id,
            instance_id=instance_id,
            previous=self._previous_session_snapshot,
            current=session_snapshot,
            media_snapshot=media_snapshot,
            streaming_measurement=streaming_measurement,
            timestamp=session_snapshot.captured_at,
        )

        self._previous_media_snapshot = media_snapshot
        self._previous_session_snapshot = session_snapshot

        return SessionObservationResult(
            media_snapshot=media_snapshot,
            session_snapshot=session_snapshot,
            streaming_measurement=streaming_measurement,
            operational_result=operational_result,
        )

    async def run_forever(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        interval_seconds: float = 5.0,
    ) -> None:
        """Continuously execute multimedia observation cycles."""

        if interval_seconds <= 0:
            raise ValueError(
                "interval_seconds must be greater than zero"
            )

        while True:
            self.run_once(
                node_id=node_id,
                instance_id=instance_id,
            )

            await asyncio.sleep(interval_seconds)
