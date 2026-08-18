"""Tests for NodeNetworkPolicyConfig."""

import pytest

from app.noc.domain.network_interface_policy import (
    NetworkInterfacePolicy,
    NetworkInterfaceRole,
)
from app.noc.domain.node_network_policy_config import (
    NodeNetworkPolicyConfig,
)


def make_policy(
    interface: str,
    role: NetworkInterfaceRole,
    *,
    expected_up: bool = True,
    critical: bool = False,
) -> NetworkInterfacePolicy:
    return NetworkInterfacePolicy(
        interface=interface,
        role=role,
        expected_up=expected_up,
        critical=critical,
    )


def make_config() -> NodeNetworkPolicyConfig:
    return NodeNetworkPolicyConfig(
        interfaces=(
            make_policy(
                "enp9s0",
                NetworkInterfaceRole.INGEST,
                critical=True,
            ),
            make_policy(
                "ens2f0",
                NetworkInterfaceRole.PUBLICATION,
                critical=True,
            ),
            make_policy(
                "ens2f1",
                NetworkInterfaceRole.BACKUP,
                expected_up=False,
            ),
        )
    )


def test_config_creation() -> None:
    config = make_config()

    assert len(config) == 3


def test_config_gets_interface_policy() -> None:
    config = make_config()

    policy = config.get("ens2f0")

    assert policy is not None
    assert policy.role is NetworkInterfaceRole.PUBLICATION
    assert policy.critical is True


def test_config_get_returns_none_for_unknown_interface() -> None:
    config = make_config()

    assert config.get("unknown0") is None


def test_config_contains_interface() -> None:
    config = make_config()

    assert "enp9s0" in config
    assert "ens2f1" in config
    assert "unknown0" not in config


def test_config_returns_required_interfaces() -> None:
    config = make_config()

    assert tuple(
        policy.interface
        for policy in config.required_interfaces
    ) == (
        "enp9s0",
        "ens2f0",
    )


def test_config_returns_optional_interfaces() -> None:
    config = make_config()

    assert tuple(
        policy.interface
        for policy in config.optional_interfaces
    ) == (
        "ens2f1",
    )


def test_config_returns_critical_interfaces() -> None:
    config = make_config()

    assert tuple(
        policy.interface
        for policy in config.critical_interfaces
    ) == (
        "enp9s0",
        "ens2f0",
    )


def test_config_accepts_empty_policy_set() -> None:
    config = NodeNetworkPolicyConfig(
        interfaces=(),
    )

    assert len(config) == 0


def test_config_rejects_non_tuple_interfaces() -> None:
    with pytest.raises(TypeError):
        NodeNetworkPolicyConfig(
            interfaces=[],  # type: ignore[arg-type]
        )


def test_config_rejects_invalid_policy_entry() -> None:
    with pytest.raises(TypeError):
        NodeNetworkPolicyConfig(
            interfaces=(
                object(),  # type: ignore[arg-type]
            ),
        )


def test_config_rejects_duplicate_interface() -> None:
    with pytest.raises(ValueError):
        NodeNetworkPolicyConfig(
            interfaces=(
                make_policy(
                    "ens2f0",
                    NetworkInterfaceRole.PUBLICATION,
                ),
                make_policy(
                    "ens2f0",
                    NetworkInterfaceRole.BACKUP,
                ),
            )
        )


def test_get_rejects_non_string_interface() -> None:
    config = make_config()

    with pytest.raises(TypeError):
        config.get(
            123  # type: ignore[arg-type]
        )


def test_get_rejects_empty_interface() -> None:
    config = make_config()

    with pytest.raises(ValueError):
        config.get("   ")
