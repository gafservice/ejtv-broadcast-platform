"""Tests del dominio especializado de salud HLS."""

import pytest

from app.domain.streaming.health import (
    HealthStatus,
    HLSSessionHealth,
)


def make_health(**overrides: object) -> HLSSessionHealth:
    values = {
        "session_id": "hls-session-1",
        "path_name": "impact",
        "state": "read",
        "effective_delta_bytes": 3_000_000,
        "effective_bitrate_mbps": 4.8,
        "status": HealthStatus.HEALTHY,
        "message": "HLS reader has observed effective traffic.",
    }
    values.update(overrides)

    return HLSSessionHealth(**values)


def test_hls_session_health_normalizes_text_fields() -> None:
    health = make_health(
        session_id="  hls-session-1  ",
        path_name="  impact  ",
        state="  read  ",
        message="  HLS healthy.  ",
    )

    assert health.session_id == "hls-session-1"
    assert health.path_name == "impact"
    assert health.state == "read"
    assert health.message == "HLS healthy."


@pytest.mark.parametrize(
    "field_name",
    (
        "session_id",
        "path_name",
        "state",
        "message",
    ),
)
def test_hls_session_health_rejects_blank_text(
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
        ("effective_bitrate_mbps", float("nan")),
    ),
)
def test_hls_session_health_rejects_invalid_numeric_evidence(
    field_name: str,
    value: object,
) -> None:
    with pytest.raises(ValueError):
        make_health(**{field_name: value})


def test_hls_session_health_is_public_streaming_domain() -> None:
    from app.domain.streaming import HLSSessionHealth as exported

    assert exported is HLSSessionHealth
