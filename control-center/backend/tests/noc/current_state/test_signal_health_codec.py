"""Contract tests for canonical Signal Health JSON codec."""

from __future__ import annotations

import json

import pytest

from app.domain.streaming.health import HealthStatus
from app.domain.streaming.signal_health import SignalHealth
from app.noc.current_state.signal_health_codec import SignalHealthCodec


def _health() -> SignalHealth:
    return SignalHealth(
        profile_id=" profile-1 ",
        service_id=" service-1 ",
        path_name=" impact ",
        media_status=HealthStatus.HEALTHY,
        transport_status=HealthStatus.DEGRADED,
        status=HealthStatus.DEGRADED,
    )


def test_encode_produces_json_with_canonical_signal_health_fields() -> None:
    codec = SignalHealthCodec()

    payload = codec.encode(_health())
    decoded = json.loads(payload)

    assert decoded == {
        "profile_id": "profile-1",
        "service_id": "service-1",
        "path_name": "impact",
        "media_status": "HEALTHY",
        "transport_status": "DEGRADED",
        "status": "DEGRADED",
    }


def test_decode_reconstructs_signal_health() -> None:
    codec = SignalHealthCodec()

    payload = json.dumps(
        {
            "profile_id": "profile-1",
            "service_id": "service-1",
            "path_name": "impact",
            "media_status": "HEALTHY",
            "transport_status": "DEGRADED",
            "status": "DEGRADED",
        }
    )

    result = codec.decode(payload)

    assert result == SignalHealth(
        profile_id="profile-1",
        service_id="service-1",
        path_name="impact",
        media_status=HealthStatus.HEALTHY,
        transport_status=HealthStatus.DEGRADED,
        status=HealthStatus.DEGRADED,
    )


def test_round_trip_preserves_signal_health() -> None:
    codec = SignalHealthCodec()
    health = _health()

    assert codec.decode(codec.encode(health)) == health


@pytest.mark.parametrize(
    "status",
    tuple(HealthStatus),
)
def test_round_trip_preserves_each_health_status(
    status: HealthStatus,
) -> None:
    codec = SignalHealthCodec()

    health = SignalHealth(
        profile_id="profile-1",
        service_id="service-1",
        path_name="impact",
        media_status=status,
        transport_status=status,
        status=status,
    )

    assert codec.decode(codec.encode(health)) == health


def test_round_trip_preserves_none_path_name() -> None:
    codec = SignalHealthCodec()

    health = SignalHealth(
        profile_id="profile-1",
        service_id="service-1",
        path_name=None,
        media_status=HealthStatus.UNKNOWN,
        transport_status=HealthStatus.UNKNOWN,
        status=HealthStatus.UNKNOWN,
    )

    assert codec.decode(codec.encode(health)) == health


def test_encode_rejects_non_signal_health() -> None:
    codec = SignalHealthCodec()

    with pytest.raises(
        TypeError,
        match="health must be a SignalHealth",
    ):
        codec.encode(object())


def test_decode_rejects_non_string_payload() -> None:
    codec = SignalHealthCodec()

    with pytest.raises(
        TypeError,
        match="payload must be a string",
    ):
        codec.decode(object())


def test_decode_rejects_non_object_json() -> None:
    codec = SignalHealthCodec()

    with pytest.raises(
        ValueError,
        match="payload must contain a JSON object",
    ):
        codec.decode("[]")


def test_decode_rejects_unknown_health_status() -> None:
    codec = SignalHealthCodec()

    payload = json.dumps(
        {
            "profile_id": "profile-1",
            "service_id": "service-1",
            "path_name": "impact",
            "media_status": "HEALTHY",
            "transport_status": "INVALID",
            "status": "DEGRADED",
        }
    )

    with pytest.raises(ValueError):
        codec.decode(payload)

def test_codec_round_trip_preserves_signal_health_reason() -> None:
    codec = SignalHealthCodec()

    health = SignalHealth(
        profile_id="profile-1",
        service_id="service-1",
        path_name="impact",
        media_status=HealthStatus.DEGRADED,
        transport_status=HealthStatus.HEALTHY,
        status=HealthStatus.DEGRADED,
        reason="media degraded",
    )

    result = codec.decode(codec.encode(health))

    assert result.reason == "media degraded"


def test_decode_legacy_payload_without_reason_defaults_to_none() -> None:
    codec = SignalHealthCodec()

    payload = json.dumps(
        {
            "profile_id": "profile-1",
            "service_id": "service-1",
            "path_name": "impact",
            "media_status": "HEALTHY",
            "transport_status": "HEALTHY",
            "status": "HEALTHY",
        }
    )

    result = codec.decode(payload)

    assert result.reason is None
