"""Tests for NodeHealthDiagnostic."""

from datetime import UTC, datetime, timedelta, timezone

import pytest

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


CAPTURED_AT = datetime(
    2026,
    8,
    18,
    23,
    0,
    tzinfo=UTC,
)


def make_interface(
    interface: str,
    state: NodeHealthState,
    *,
    observed_at: datetime = CAPTURED_AT,
) -> NetworkInterfaceHealth:
    return NetworkInterfaceHealth(
        interface=interface,
        state=state,
        observed_at=observed_at,
        reason="Test interface health",
    )


def make_diagnostic(
    **overrides,
) -> NodeHealthDiagnostic:
    values = {
        "captured_at": CAPTURED_AT,
        "health": NodeHealth(
            NodeHealthState.WARNING
        ),
        "system_health": NodeHealth(
            NodeHealthState.HEALTHY
        ),
        "network_health": NodeHealth(
            NodeHealthState.WARNING
        ),
        "network_interfaces": (
            make_interface(
                "enp9s0",
                NodeHealthState.HEALTHY,
            ),
            make_interface(
                "ens2f0",
                NodeHealthState.WARNING,
            ),
        ),
    }

    values.update(overrides)

    return NodeHealthDiagnostic(**values)


def test_creation() -> None:
    diagnostic = make_diagnostic()

    assert diagnostic.captured_at == CAPTURED_AT
    assert (
        diagnostic.health.state
        is NodeHealthState.WARNING
    )
    assert diagnostic.interface_count == 2


def test_unhealthy_interfaces() -> None:
    diagnostic = make_diagnostic()

    unhealthy = diagnostic.unhealthy_interfaces

    assert len(unhealthy) == 1
    assert unhealthy[0].interface == "ens2f0"


def test_accepts_empty_interfaces() -> None:
    diagnostic = make_diagnostic(
        network_interfaces=(),
    )

    assert diagnostic.interface_count == 0
    assert diagnostic.unhealthy_interfaces == ()


def test_rejects_naive_captured_at() -> None:
    with pytest.raises(ValueError):
        make_diagnostic(
            captured_at=datetime(
                2026,
                8,
                18,
                23,
                0,
            ),
            network_interfaces=(),
        )


def test_rejects_non_utc_captured_at() -> None:
    with pytest.raises(ValueError):
        make_diagnostic(
            captured_at=datetime(
                2026,
                8,
                18,
                23,
                0,
                tzinfo=UTC,
            ).astimezone(
                timezone(
                    timedelta(hours=-6)
                )
            ),
            network_interfaces=(),
        )


@pytest.mark.parametrize(
    "field",
    (
        "health",
        "system_health",
        "network_health",
    ),
)
def test_rejects_invalid_health(
    field: str,
) -> None:
    with pytest.raises(TypeError):
        make_diagnostic(
            **{
                field: object(),
            }
        )


def test_rejects_non_tuple_interfaces() -> None:
    with pytest.raises(TypeError):
        make_diagnostic(
            network_interfaces=[],  # type: ignore[arg-type]
        )


def test_rejects_invalid_interface_member() -> None:
    with pytest.raises(TypeError):
        make_diagnostic(
            network_interfaces=(
                object(),  # type: ignore[arg-type]
            ),
        )


def test_rejects_duplicate_interfaces() -> None:
    with pytest.raises(ValueError):
        make_diagnostic(
            network_interfaces=(
                make_interface(
                    "ens2f0",
                    NodeHealthState.HEALTHY,
                ),
                make_interface(
                    "ens2f0",
                    NodeHealthState.WARNING,
                ),
            ),
        )


def test_rejects_interface_timestamp_mismatch() -> None:
    with pytest.raises(ValueError):
        make_diagnostic(
            network_interfaces=(
                make_interface(
                    "ens2f0",
                    NodeHealthState.WARNING,
                    observed_at=(
                        CAPTURED_AT
                        + timedelta(seconds=1)
                    ),
                ),
            ),
        )
