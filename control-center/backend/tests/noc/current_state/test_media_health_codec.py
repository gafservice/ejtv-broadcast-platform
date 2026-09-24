"""Contract tests for MediaHealth JSON current-state codec.

ENG-013C — Media Health Current State

The codec preserves the complete MediaHealth value:

- media identity;
- aggregate HealthStatus;
- optional container/video/audio component Health values.

Persistence and current-state replacement semantics belong to the
repository, not to this codec.
"""

from __future__ import annotations

import json

import pytest

from app.domain.streaming.health import HealthStatus
from app.domain.streaming.media_health import (
    MediaComponentHealth,
    MediaHealth,
)
from app.noc.current_state.media_health_codec import (
    MediaHealthCodec,
)


def _complete_health() -> MediaHealth:
    return MediaHealth(
        profile_id="impact-main",
        service_id="impact",
        path_name="impact",
        status=HealthStatus.DEGRADED,
        container=MediaComponentHealth(
            component="container",
            status=HealthStatus.HEALTHY,
        ),
        video=MediaComponentHealth(
            component="video",
            status=HealthStatus.DEGRADED,
        ),
        audio=MediaComponentHealth(
            component="audio",
            status=HealthStatus.HEALTHY,
        ),
    )


def test_round_trip_preserves_complete_media_health() -> None:
    health = _complete_health()

    payload = MediaHealthCodec.encode(health)

    assert MediaHealthCodec.decode(payload) == health


def test_round_trip_preserves_absent_optional_components() -> None:
    health = MediaHealth(
        profile_id="impact-main",
        service_id="impact",
        path_name="impact",
        status=HealthStatus.UNKNOWN,
    )

    payload = MediaHealthCodec.encode(health)

    assert MediaHealthCodec.decode(payload) == health


def test_round_trip_preserves_none_path_name() -> None:
    health = MediaHealth(
        profile_id="profile-1",
        service_id="service-1",
        path_name=None,
        status=HealthStatus.HEALTHY,
    )

    payload = MediaHealthCodec.encode(health)

    assert MediaHealthCodec.decode(payload) == health


def test_encode_is_deterministic_compact_json() -> None:
    health = _complete_health()

    first = MediaHealthCodec.encode(health)
    second = MediaHealthCodec.encode(health)

    assert first == second
    assert "\n" not in first
    assert ": " not in first
    assert ", " not in first

    raw = json.loads(first)

    assert raw == {
        "audio": {
            "component": "audio",
            "status": "HEALTHY",
        },
        "container": {
            "component": "container",
            "status": "HEALTHY",
        },
        "path_name": "impact",
        "profile_id": "impact-main",
        "service_id": "impact",
        "status": "DEGRADED",
        "video": {
            "component": "video",
            "status": "DEGRADED",
        },
    }


def test_encode_rejects_wrong_type() -> None:
    with pytest.raises(TypeError):
        MediaHealthCodec.encode("not-media-health")  # type: ignore[arg-type]


def test_decode_rejects_non_string_payload() -> None:
    with pytest.raises(TypeError):
        MediaHealthCodec.decode(123)  # type: ignore[arg-type]


def test_decode_rejects_non_object_json() -> None:
    with pytest.raises(ValueError):
        MediaHealthCodec.decode("[]")


def test_decode_rejects_invalid_health_status() -> None:
    payload = json.dumps(
        {
            "profile_id": "impact-main",
            "service_id": "impact",
            "path_name": "impact",
            "status": "not-a-health-status",
            "container": None,
            "video": None,
            "audio": None,
        }
    )

    with pytest.raises((ValueError, KeyError)):
        MediaHealthCodec.decode(payload)


def test_decode_rejects_invalid_component_shape() -> None:
    payload = json.dumps(
        {
            "profile_id": "impact-main",
            "service_id": "impact",
            "path_name": "impact",
            "status": "HEALTHY",
            "container": {
                "component": "container",
            },
            "video": None,
            "audio": None,
        }
    )

    with pytest.raises((ValueError, KeyError)):
        MediaHealthCodec.decode(payload)
