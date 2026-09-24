"""JSON codec for MediaHealth current state.

ENG-013C — Media Health Current State

The codec provides an explicit, deterministic representation of
MediaHealth values stored in shared current-state storage.

It does not define persistence, history, evidence or runtime ownership.
"""

from __future__ import annotations

import json
from typing import Any

from app.domain.streaming.health import HealthStatus
from app.domain.streaming.media_health import (
    MediaComponentHealth,
    MediaHealth,
)


class MediaHealthCodec:
    """Encode and decode MediaHealth values as JSON."""

    @staticmethod
    def encode(
        health: MediaHealth,
    ) -> str:
        if not isinstance(health, MediaHealth):
            raise TypeError(
                "health must be a MediaHealth"
            )

        payload = {
            "profile_id": health.profile_id,
            "service_id": health.service_id,
            "path_name": health.path_name,
            "status": health.status.value,
            "container": MediaHealthCodec._encode_component(
                health.container
            ),
            "video": MediaHealthCodec._encode_component(
                health.video
            ),
            "audio": MediaHealthCodec._encode_component(
                health.audio
            ),
        }

        return json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        )

    @staticmethod
    def decode(
        payload: str,
    ) -> MediaHealth:
        if not isinstance(payload, str):
            raise TypeError(
                "payload must be a string"
            )

        raw: Any = json.loads(payload)

        if not isinstance(raw, dict):
            raise ValueError(
                "MediaHealth payload must be an object"
            )

        return MediaHealth(
            profile_id=raw["profile_id"],
            service_id=raw["service_id"],
            path_name=raw["path_name"],
            status=HealthStatus(
                raw["status"]
            ),
            container=MediaHealthCodec._decode_component(
                raw["container"]
            ),
            video=MediaHealthCodec._decode_component(
                raw["video"]
            ),
            audio=MediaHealthCodec._decode_component(
                raw["audio"]
            ),
        )

    @staticmethod
    def _encode_component(
        component: MediaComponentHealth | None,
    ) -> dict[str, str] | None:
        if component is None:
            return None

        if not isinstance(
            component,
            MediaComponentHealth,
        ):
            raise TypeError(
                "component must be a MediaComponentHealth or None"
            )

        return {
            "component": component.component,
            "status": component.status.value,
        }

    @staticmethod
    def _decode_component(
        raw: Any,
    ) -> MediaComponentHealth | None:
        if raw is None:
            return None

        if not isinstance(raw, dict):
            raise ValueError(
                "MediaHealth component must be an object or null"
            )

        return MediaComponentHealth(
            component=raw["component"],
            status=HealthStatus(
                raw["status"]
            ),
        )
