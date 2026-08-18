"""Tests for network interface operational policy."""

import pytest

from app.noc.domain.network_interface_policy import (
    NetworkInterfacePolicy,
    NetworkInterfaceRole,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    (
        ("INGEST", NetworkInterfaceRole.INGEST),
        ("publication", NetworkInterfaceRole.PUBLICATION),
        (" management ", NetworkInterfaceRole.MANAGEMENT),
        ("backup", NetworkInterfaceRole.BACKUP),
        ("test", NetworkInterfaceRole.TEST),
        ("loopback", NetworkInterfaceRole.LOOPBACK),
        ("other", NetworkInterfaceRole.OTHER),
    ),
)
def test_role_from_value(
    value: str,
    expected: NetworkInterfaceRole,
) -> None:
    assert NetworkInterfaceRole.from_value(value) is expected


def test_role_rejects_non_string() -> None:
    with pytest.raises(TypeError):
        NetworkInterfaceRole.from_value(
            123  # type: ignore[arg-type]
        )


def test_role_rejects_empty_value() -> None:
    with pytest.raises(ValueError):
        NetworkInterfaceRole.from_value("   ")


def test_role_rejects_unknown_value() -> None:
    with pytest.raises(ValueError):
        NetworkInterfaceRole.from_value("INVALID")


def test_policy_creation() -> None:
    policy = NetworkInterfacePolicy(
        interface="ens2f0",
        role=NetworkInterfaceRole.PUBLICATION,
        expected_up=True,
        critical=True,
    )

    assert policy.interface == "ens2f0"
    assert policy.role is NetworkInterfaceRole.PUBLICATION
    assert policy.expected_up is True
    assert policy.critical is True
    assert policy.is_required is True
    assert policy.is_optional is False


def test_policy_normalizes_interface() -> None:
    policy = NetworkInterfacePolicy(
        interface="  enp9s0  ",
        role=NetworkInterfaceRole.INGEST,
    )

    assert policy.interface == "enp9s0"


def test_optional_interface() -> None:
    policy = NetworkInterfacePolicy(
        interface="ens2f1",
        role=NetworkInterfaceRole.BACKUP,
        expected_up=False,
        critical=False,
    )

    assert policy.is_required is False
    assert policy.is_optional is True


def test_policy_rejects_empty_interface() -> None:
    with pytest.raises(ValueError):
        NetworkInterfacePolicy(
            interface="   ",
            role=NetworkInterfaceRole.INGEST,
        )


def test_policy_rejects_invalid_interface_type() -> None:
    with pytest.raises(TypeError):
        NetworkInterfacePolicy(
            interface=123,  # type: ignore[arg-type]
            role=NetworkInterfaceRole.INGEST,
        )


def test_policy_rejects_invalid_role() -> None:
    with pytest.raises(TypeError):
        NetworkInterfacePolicy(
            interface="ens2f0",
            role="PUBLICATION",  # type: ignore[arg-type]
        )


def test_policy_rejects_invalid_expected_up() -> None:
    with pytest.raises(TypeError):
        NetworkInterfacePolicy(
            interface="ens2f0",
            role=NetworkInterfaceRole.PUBLICATION,
            expected_up=1,  # type: ignore[arg-type]
        )


def test_policy_rejects_invalid_critical() -> None:
    with pytest.raises(TypeError):
        NetworkInterfacePolicy(
            interface="ens2f0",
            role=NetworkInterfaceRole.PUBLICATION,
            critical=1,  # type: ignore[arg-type]
        )
