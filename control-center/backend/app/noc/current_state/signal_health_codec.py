"""JSON codec for canonical Signal Health state."""

from __future__ import annotations

import json
from typing import Any

from app.domain.streaming.health import HealthStatus
from app.domain.streaming.signal_health import SignalHealth


class SignalHealthCodec:
    """Serialize and reconstruct canonical SignalHealth values."""

    def encode(self, health: SignalHealth) -> str:
        if not isinstance(health, SignalHealth):
            raise TypeError("health must be a SignalHealth")

        payload = {
            "profile_id": health.profile_id,
            "service_id": health.service_id,
            "path_name": health.path_name,
            "media_status": health.media_status.value,
            "transport_status": health.transport_status.value,
            "status": health.status.value,
        }

        return json.dumps(payload)

    def decode(self, payload: str) -> SignalHealth:
        if not isinstance(payload, str):
            raise TypeError("payload must be a string")

        raw: Any = json.loads(payload)

        if not isinstance(raw, dict):
            raise ValueError("payload must contain a JSON object")

        return SignalHealth(
            profile_id=raw["profile_id"],
            service_id=raw["service_id"],
            path_name=raw["path_name"],
            media_status=HealthStatus(raw["media_status"]),
            transport_status=HealthStatus(raw["transport_status"]),
            status=HealthStatus(raw["status"]),
        )
