"""Tests de los modelos del panel NETWORK INTERFACES."""

from datetime import UTC, datetime

import pytest

from app.dashboard.models import (
    NetworkInterfaceRowData,
    NetworkInterfacesPanelData,
)


def make_row(
    interface: str = "ens2f0",
) -> NetworkInterfaceRowData:
    return NetworkInterfaceRowData(
        interface=interface,
        interface_type="ETHERNET",
        is_up=True,
        carrier=True,
        link_speed_mbps=1000,
        mtu=1500,
        mac_address="00:e0:ed:2c:6d:c0",
        ipv4_addresses=("172.16.30.35",),
        ipv6_addresses=(
            "fe80::2c18:255d:9960:44ab",
        ),
        rx_bps=1_000_000.0,
        tx_bps=2_000_000.0,
        errors_in=0,
        errors_out=0,
        dropped_in=10,
        dropped_out=0,
        errors_in_per_second=0.0,
        errors_out_per_second=0.0,
        dropped_in_per_second=0.5,
        dropped_out_per_second=0.0,
    )


def test_network_interface_row_creation() -> None:
    row = make_row()

    assert row.interface == "ens2f0"
    assert row.interface_type == "ETHERNET"
    assert row.is_up is True
    assert row.carrier is True
    assert row.link_speed_mbps == 1000
    assert row.mtu == 1500
    assert row.rx_bps == 1_000_000.0
    assert row.tx_bps == 2_000_000.0


def test_network_interface_row_normalizes_strings() -> None:
    row = make_row(
        interface="  ens2f0  ",
    )

    assert row.interface == "ens2f0"


def test_network_interface_row_rejects_empty_interface() -> None:
    with pytest.raises(ValueError):
        make_row(interface="   ")


def test_network_interfaces_panel_creation() -> None:
    captured_at = datetime.now(UTC)

    panel = NetworkInterfacesPanelData(
        interfaces=(
            make_row("enp9s0"),
            make_row("ens2f0"),
        ),
        captured_at=captured_at,
    )

    assert len(panel.interfaces) == 2
    assert panel.captured_at == captured_at


def test_network_interfaces_panel_accepts_empty_collection() -> None:
    panel = NetworkInterfacesPanelData(
        interfaces=(),
        captured_at=datetime.now(UTC),
    )

    assert panel.interfaces == ()


def test_network_interfaces_panel_rejects_duplicate_interfaces() -> None:
    with pytest.raises(ValueError):
        NetworkInterfacesPanelData(
            interfaces=(
                make_row("ens2f0"),
                make_row("ens2f0"),
            ),
            captured_at=datetime.now(UTC),
        )


def test_network_interfaces_panel_requires_tuple() -> None:
    with pytest.raises(ValueError):
        NetworkInterfacesPanelData(
            interfaces=[  # type: ignore[arg-type]
                make_row(),
            ],
            captured_at=datetime.now(UTC),
        )


def test_network_interfaces_panel_requires_timezone() -> None:
    with pytest.raises(ValueError):
        NetworkInterfacesPanelData(
            interfaces=(
                make_row(),
            ),
            captured_at=datetime.now(),
        )
