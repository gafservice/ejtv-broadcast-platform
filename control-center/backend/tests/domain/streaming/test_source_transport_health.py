"""Domain contract for source transport health.

ENG-013C — Source Transport Health Contract v1

Source Transport Health represents an already-evaluated conclusion about
the transport that feeds one logical multimedia signal.

It is intentionally independent from client/delivery sessions and from
protocol-specific metrics.
"""

from __future__ import annotations

import pytest

from app.domain.streaming.health import HealthStatus
from app.domain.streaming.source_transport_health import (
    SourceTransportHealth,
)


def build_health(
    *,
    service_id: str = "impact",
    path_name: str = "impact",
    source_type: str = "srtSource",
    status: HealthStatus = HealthStatus.HEALTHY,
) -> SourceTransportHealth:
    return SourceTransportHealth(
        service_id=service_id,
        path_name=path_name,
        source_type=source_type,
        status=status,
    )


def test_preserves_source_transport_identity() -> None:
    health = build_health()

    assert health.service_id == "impact"
    assert health.path_name == "impact"
    assert health.source_type == "srtSource"


@pytest.mark.parametrize(
    "status",
    (
        HealthStatus.UNKNOWN,
        HealthStatus.HEALTHY,
        HealthStatus.DEGRADED,
        HealthStatus.CRITICAL,
    ),
)
def test_reuses_canonical_health_status(
    status: HealthStatus,
) -> None:
    health = build_health(status=status)

    assert health.status is status


def test_identity_is_normalized() -> None:
    health = build_health(
        service_id="  impact  ",
        path_name="  impact  ",
        source_type="  srtSource  ",
    )

    assert health.service_id == "impact"
    assert health.path_name == "impact"
    assert health.source_type == "srtSource"


@pytest.mark.parametrize(
    ("field_name", "kwargs"),
    (
        (
            "service_id",
            {"service_id": "   "},
        ),
        (
            "path_name",
            {"path_name": "   "},
        ),
        (
            "source_type",
            {"source_type": "   "},
        ),
    ),
)
def test_rejects_blank_identity_fields(
    field_name: str,
    kwargs: dict[str, str],
) -> None:
    with pytest.raises(
        ValueError,
        match=field_name,
    ):
        build_health(**kwargs)


def test_rejects_non_health_status() -> None:
    with pytest.raises(
        TypeError,
        match="status",
    ):
        SourceTransportHealth(
            service_id="impact",
            path_name="impact",
            source_type="srtSource",
            status="HEALTHY",  # type: ignore[arg-type]
        )


def test_source_type_is_descriptive_not_protocol_specific() -> None:
    health = build_health(
        service_id="future-signal",
        path_name="future-path",
        source_type="rtmpSource",
    )

    assert health.source_type == "rtmpSource"


@pytest.mark.parametrize(
    "source_type",
    (
        "srtSource",
        "rtmpSource",
        "rtspSource",
        "mpegtsSource",
        "udpSource",
        "futureSource",
    ),
)
def test_domain_does_not_hardcode_source_protocols(
    source_type: str,
) -> None:
    health = build_health(
        source_type=source_type,
    )

    assert health.source_type == source_type


def test_contract_does_not_expose_client_session_identity() -> None:
    fields = SourceTransportHealth.__dataclass_fields__

    assert "session_id" not in fields
    assert "connection_id" not in fields
    assert "remote_address" not in fields
    assert "role" not in fields


def test_contract_does_not_expose_protocol_specific_metrics() -> None:
    fields = SourceTransportHealth.__dataclass_fields__

    assert "rtt_ms" not in fields
    assert "packet_loss_rate" not in fields
    assert "retransmission_rate" not in fields


def test_contract_does_not_expose_media_evidence() -> None:
    fields = SourceTransportHealth.__dataclass_fields__

    assert "codec" not in fields
    assert "gop" not in fields
    assert "pcr" not in fields
    assert "mpegts" not in fields
