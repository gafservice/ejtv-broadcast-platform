from datetime import datetime, timezone

import pytest

from app.noc.current_state.node_health_diagnostic_codec import (
    NodeHealthDiagnosticCodec,
)
from app.noc.domain.network_interface_health import (
    NetworkInterfaceHealth,
)
from app.noc.domain.node_health import (
    NodeHealth,
    NodeHealthState,
)
from app.noc.domain.node_health_diagnostic import (
    NodeHealthDiagnostic,
)


def _diagnostic() -> NodeHealthDiagnostic:
    captured_at = datetime(
        2026,
        9,
        3,
        12,
        34,
        56,
        123456,
        tzinfo=timezone.utc,
    )

    return NodeHealthDiagnostic(
        captured_at=captured_at,
        health=NodeHealth(
            NodeHealthState.DEGRADED
        ),
        system_health=NodeHealth(
            NodeHealthState.WARNING
        ),
        network_health=NodeHealth(
            NodeHealthState.CRITICAL
        ),
        network_interfaces=(
            NetworkInterfaceHealth(
                interface="ens2f0",
                state=NodeHealthState.HEALTHY,
                observed_at=captured_at,
                reason="carrier and traffic healthy",
                carrier_ok=True,
                traffic_ok=True,
                error_rate=0.001,
                drop_rate=0.002,
            ),
            NetworkInterfaceHealth(
                interface="ens2f1",
                state=NodeHealthState.WARNING,
                observed_at=captured_at,
                reason="no recent traffic",
                carrier_ok=True,
                traffic_ok=False,
                error_rate=None,
                drop_rate=None,
            ),
        ),
    )


def test_round_trip_preserves_complete_diagnostic() -> None:
    diagnostic = _diagnostic()

    payload = NodeHealthDiagnosticCodec.encode(
        diagnostic
    )
    decoded = NodeHealthDiagnosticCodec.decode(
        payload
    )

    assert decoded == diagnostic


def test_round_trip_preserves_empty_interfaces() -> None:
    captured_at = datetime(
        2026,
        9,
        3,
        12,
        0,
        tzinfo=timezone.utc,
    )

    diagnostic = NodeHealthDiagnostic(
        captured_at=captured_at,
        health=NodeHealth(
            NodeHealthState.UNKNOWN
        ),
        system_health=NodeHealth(
            NodeHealthState.UNKNOWN
        ),
        network_health=NodeHealth(
            NodeHealthState.UNKNOWN
        ),
    )

    decoded = NodeHealthDiagnosticCodec.decode(
        NodeHealthDiagnosticCodec.encode(
            diagnostic
        )
    )

    assert decoded == diagnostic
    assert decoded.network_interfaces == ()


def test_encode_rejects_non_diagnostic() -> None:
    with pytest.raises(
        TypeError,
        match="diagnostic must be a NodeHealthDiagnostic",
    ):
        NodeHealthDiagnosticCodec.encode(
            object()  # type: ignore[arg-type]
        )


def test_decode_rejects_non_object_json() -> None:
    with pytest.raises(
        ValueError,
        match="payload must be an object",
    ):
        NodeHealthDiagnosticCodec.decode(
            "[]"
        )
