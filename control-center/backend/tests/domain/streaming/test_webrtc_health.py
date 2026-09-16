"""Tests del modelo especializado de salud WebRTC."""

import pytest

from app.domain.streaming import (
    HealthStatus,
    WebRTCSessionHealth,
)


def make_health(**overrides: object) -> WebRTCSessionHealth:
    values: dict[str, object] = {
        "session_id": "webrtc-session-1",
        "path_name": "impact",
        "state": "read",
        "effective_delta_bytes": 7_500_000,
        "effective_bitrate_mbps": 6.0,
        "status": HealthStatus.HEALTHY,
        "message": "WebRTC reader has observed effective traffic.",
    }
    values.update(overrides)
    return WebRTCSessionHealth(**values)


def test_webrtc_health_preserves_observed_evidence() -> None:
    health = make_health()

    assert health.session_id == "webrtc-session-1"
    assert health.path_name == "impact"
    assert health.state == "read"
    assert health.effective_delta_bytes == 7_500_000
    assert health.effective_bitrate_mbps == pytest.approx(6.0)
    assert health.status is HealthStatus.HEALTHY
    assert health.message == "WebRTC reader has observed effective traffic."


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("session_id", " "),
        ("path_name", ""),
        ("state", " "),
        ("message", ""),
    ],
)
def test_webrtc_health_rejects_blank_required_text(
    field: str,
    value: object,
) -> None:
    with pytest.raises(ValueError):
        make_health(**{field: value})


def test_webrtc_health_rejects_negative_effective_delta() -> None:
    with pytest.raises(ValueError):
        make_health(effective_delta_bytes=-1)


@pytest.mark.parametrize(
    "value",
    [
        -0.1,
        float("inf"),
        float("-inf"),
        float("nan"),
    ],
)
def test_webrtc_health_rejects_invalid_effective_bitrate(
    value: float,
) -> None:
    with pytest.raises(ValueError):
        make_health(effective_bitrate_mbps=value)


def test_webrtc_health_is_exported_from_streaming_domain() -> None:
    from app.domain.streaming import WebRTCSessionHealth as exported

    assert exported is WebRTCSessionHealth
