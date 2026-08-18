"""Tests para NetworkInterfacesPanelRenderer."""

from datetime import UTC, datetime

from rich.console import Console
from rich.panel import Panel

from app.dashboard.models import (
    NetworkInterfaceRowData,
    NetworkInterfacesPanelData,
)
from app.dashboard.renderers.network_interfaces_panel_renderer import (
    NetworkInterfacesPanelRenderer,
)


def make_panel_data() -> NetworkInterfacesPanelData:
    captured_at = datetime(
        2026,
        8,
        18,
        20,
        0,
        tzinfo=UTC,
    )

    return NetworkInterfacesPanelData(
        interfaces=(
            NetworkInterfaceRowData(
                interface="enp9s0",
                interface_type="ETHERNET",
                is_up=True,
                carrier=True,
                link_speed_mbps=1000,
                mtu=1500,
                mac_address="3c:07:54:7c:b5:88",
                ipv4_addresses=("10.0.18.54",),
                ipv6_addresses=(),
                rx_bps=9_000_000.0,
                tx_bps=418.0,
                errors_in=6,
                errors_out=0,
                dropped_in=0,
                dropped_out=89,
                dropped_in_per_second=0.0,
            ),
            NetworkInterfaceRowData(
                interface="ens2f0",
                interface_type="ETHERNET",
                is_up=True,
                carrier=True,
                link_speed_mbps=100,
                mtu=1500,
                mac_address="00:e0:ed:2c:6d:c0",
                ipv4_addresses=("172.16.30.35",),
                ipv6_addresses=(),
                rx_bps=59_800.0,
                tx_bps=4_920_000.0,
                errors_in=0,
                errors_out=0,
                dropped_in=100,
                dropped_out=0,
                dropped_in_per_second=0.5,
            ),
            NetworkInterfaceRowData(
                interface="ens2f1",
                interface_type="ETHERNET",
                is_up=False,
                carrier=False,
                link_speed_mbps=None,
                mtu=1500,
                mac_address="00:e0:ed:2c:6d:c1",
                ipv4_addresses=(),
                ipv6_addresses=(),
                rx_bps=0.0,
                tx_bps=0.0,
                errors_in=0,
                errors_out=0,
                dropped_in=0,
                dropped_out=0,
                dropped_in_per_second=0.0,
            ),
            NetworkInterfaceRowData(
                interface="lo",
                interface_type="LOOPBACK",
                is_up=True,
                carrier=True,
                link_speed_mbps=None,
                mtu=65536,
                mac_address="00:00:00:00:00:00",
                ipv4_addresses=("127.0.0.1",),
                ipv6_addresses=("::1",),
                rx_bps=246_000.0,
                tx_bps=246_000.0,
                errors_in=0,
                errors_out=0,
                dropped_in=0,
                dropped_out=0,
                dropped_in_per_second=0.0,
            ),
        ),
        captured_at=captured_at,
    )


def render_text() -> str:
    renderer = NetworkInterfacesPanelRenderer()

    console = Console(
        record=True,
        width=160,
        color_system=None,
    )

    console.print(
        renderer.render(
            make_panel_data()
        )
    )

    return console.export_text()


def test_renderer_returns_panel() -> None:
    renderer = NetworkInterfacesPanelRenderer()

    result = renderer.render(
        make_panel_data()
    )

    assert isinstance(result, Panel)


def test_renderer_contains_interfaces() -> None:
    output = render_text()

    assert "NETWORK INTERFACES" in output

    assert "enp9s0" in output
    assert "ens2f0" in output
    assert "ens2f1" in output
    assert "lo" in output


def test_renderer_formats_interface_types() -> None:
    output = render_text()

    assert "ETH" in output
    assert "LOOP" in output


def test_renderer_formats_states() -> None:
    output = render_text()

    assert "UP" in output
    assert "DOWN" in output


def test_renderer_formats_link_speed() -> None:
    output = render_text()

    assert "1 Gbps" in output
    assert "100 Mbps" in output


def test_renderer_formats_rates() -> None:
    output = render_text()

    assert "9.00 Mbps" in output
    assert "4.92 Mbps" in output
    assert "59.80 Kbps" in output
    assert "418 bps" in output
    assert "0.50/s" in output


def test_renderer_handles_first_capture() -> None:
    row = NetworkInterfaceRowData(
        interface="wlan0",
        interface_type="WIFI",
        is_up=True,
        carrier=True,
        link_speed_mbps=None,
        mtu=1500,
        mac_address=None,
        ipv4_addresses=(),
        ipv6_addresses=(),
        rx_bps=None,
        tx_bps=None,
        errors_in=0,
        errors_out=0,
        dropped_in=0,
        dropped_out=0,
    )

    data = NetworkInterfacesPanelData(
        interfaces=(row,),
        captured_at=datetime.now(UTC),
    )

    console = Console(
        record=True,
        width=120,
        color_system=None,
    )

    console.print(
        NetworkInterfacesPanelRenderer().render(data)
    )

    output = console.export_text()

    assert "wlan0" in output
    assert "WIFI" in output
    assert "N/D" in output
