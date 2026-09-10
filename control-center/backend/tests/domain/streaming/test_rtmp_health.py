"""Tests del dominio especializado de salud RTMP."""

import pytest

from app.domain.streaming.health import (
    HealthStatus,
    RTMPConnectionHealth,
)


def make_health(**overrides: object) -> RTMPConnectionHealth:
    values = {
        "connection_id": "rtmp-conn-1",
        "path_name": "rtmp-block8-lab",
        "state": "publish",
        "effective_delta_bytes": 1_443_033,
        "effective_bitrate_mbps": 1.1544264,
        "outbound_frames_discarded": 0,
        "status": HealthStatus.HEALTHY,
        "message": "RTMP connection has observed effective traffic.",
    }
    values.update(overrides)
    return RTMPConnectionHealth(**values)


def test_rtmp_connection_health_normalizes_text_fields() -> None:
    health = make_health(
        connection_id="  rtmp-conn-1  ",
        path_name="  rtmp-block8-lab  ",
        state="  publish  ",
        message="  RTMP healthy.  ",
    )

    assert health.connection_id == "rtmp-conn-1"
    assert health.path_name == "rtmp-block8-lab"
    assert health.state == "publish"
    assert health.message == "RTMP healthy."


@pytest.mark.parametrize(
    "field_name",
    (
        "connection_id",
        "path_name",
        "state",
        "message",
    ),
)
def test_rtmp_connection_health_rejects_blank_text(
    field_name: str,
) -> None:
    with pytest.raises(ValueError):
        make_health(**{field_name: "   "})


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("effective_delta_bytes", -1),
        ("effective_bitrate_mbps", -0.1),
        ("effective_bitrate_mbps", float("inf")),
        ("outbound_frames_discarded", -1),
    ),
)
def test_rtmp_connection_health_rejects_invalid_numeric_evidence(
    field_name: str,
    value: object,
) -> None:
    with pytest.raises(ValueError):
        make_health(**{field_name: value})


def test_rtmp_connection_health_is_public_streaming_domain() -> None:
    from app.domain.streaming import RTMPConnectionHealth as exported

    assert exported is RTMPConnectionHealth
