"""Tests para NetworkInterfaceInfo."""

import pytest

from app.domain.system import (
    NetworkInterfaceInfo,
    NetworkInterfaceType,
)


def make_interface() -> NetworkInterfaceInfo:
    return NetworkInterfaceInfo(
        interface="ens2f0",
        interface_type=NetworkInterfaceType.ETHERNET,
        is_up=True,
        carrier=True,
        mtu=1500,
        mac_address="00:e0:ed:2c:6d:c0",
        link_speed_mbps=100,
        duplex="full",
        ipv4_addresses=("172.16.30.35",),
        ipv6_addresses=(
            "fe80::2c18:255d:9960:44ab",
        ),
    )


def test_network_interface_creation() -> None:
    interface = make_interface()

    assert interface.interface == "ens2f0"
    assert interface.interface_type is (
        NetworkInterfaceType.ETHERNET
    )
    assert interface.is_up is True
    assert interface.carrier is True
    assert interface.mtu == 1500
    assert interface.link_speed_mbps == 100
    assert interface.duplex == "full"


def test_network_interface_accepts_optional_link_data() -> None:
    interface = NetworkInterfaceInfo(
        interface="lo",
        interface_type=NetworkInterfaceType.LOOPBACK,
        is_up=True,
        carrier=None,
        mtu=65536,
    )

    assert interface.mac_address is None
    assert interface.link_speed_mbps is None
    assert interface.duplex is None


def test_network_interface_strips_interface_name() -> None:
    interface = NetworkInterfaceInfo(
        interface="  ens2f0  ",
        interface_type=NetworkInterfaceType.ETHERNET,
        is_up=True,
        carrier=True,
        mtu=1500,
    )

    assert interface.interface == "ens2f0"


def test_network_interface_rejects_empty_name() -> None:
    with pytest.raises(ValueError):
        NetworkInterfaceInfo(
            interface="   ",
            interface_type=NetworkInterfaceType.UNKNOWN,
            is_up=False,
            carrier=None,
            mtu=1500,
        )


def test_network_interface_rejects_invalid_type() -> None:
    with pytest.raises(TypeError):
        NetworkInterfaceInfo(
            interface="ens2f0",
            interface_type="ETHERNET",  # type: ignore[arg-type]
            is_up=True,
            carrier=True,
            mtu=1500,
        )


@pytest.mark.parametrize(
    "mtu",
    [0, -1],
)
def test_network_interface_rejects_invalid_mtu(
    mtu: int,
) -> None:
    with pytest.raises(ValueError):
        NetworkInterfaceInfo(
            interface="ens2f0",
            interface_type=NetworkInterfaceType.ETHERNET,
            is_up=True,
            carrier=True,
            mtu=mtu,
        )


def test_network_interface_rejects_negative_link_speed() -> None:
    with pytest.raises(ValueError):
        NetworkInterfaceInfo(
            interface="ens2f0",
            interface_type=NetworkInterfaceType.ETHERNET,
            is_up=True,
            carrier=True,
            mtu=1500,
            link_speed_mbps=-1,
        )


def test_network_interface_validates_ip_collections() -> None:
    with pytest.raises(TypeError):
        NetworkInterfaceInfo(
            interface="ens2f0",
            interface_type=NetworkInterfaceType.ETHERNET,
            is_up=True,
            carrier=True,
            mtu=1500,
            ipv4_addresses=[  # type: ignore[arg-type]
                "172.16.30.35",
            ],
        )


def test_network_interface_supports_wifi_type() -> None:
    interface = NetworkInterfaceInfo(
        interface="wlp3s0",
        interface_type=NetworkInterfaceType.WIFI,
        is_up=True,
        carrier=True,
        mtu=1500,
        link_speed_mbps=866,
    )

    assert interface.interface_type is (
        NetworkInterfaceType.WIFI
    )


def test_network_interface_supports_virtual_types() -> None:
    assert NetworkInterfaceType.BRIDGE.value == "BRIDGE"
    assert NetworkInterfaceType.BOND.value == "BOND"
    assert NetworkInterfaceType.VLAN.value == "VLAN"
    assert NetworkInterfaceType.TUNNEL.value == "TUNNEL"
    assert NetworkInterfaceType.VIRTUAL.value == "VIRTUAL"
