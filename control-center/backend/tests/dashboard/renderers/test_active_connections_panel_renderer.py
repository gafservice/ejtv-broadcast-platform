"""Pruebas del renderizador CONNECTED CLIENTS."""

from datetime import datetime, timezone

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from app.dashboard.models import (
    ActiveConnectionRow,
    ActiveConnectionsPanelData,
)
from app.dashboard.renderers.active_connections_panel_renderer import (
    ActiveConnectionsPanelRenderer,
)


def build_panel() -> ActiveConnectionsPanelData:
    connection = ActiveConnectionRow(
        remote_address="201.192.154.130:26676",
        country="Costa Rica",
        country_code="CR",
        asn=17054,
        provider="RACSA",
        protocol="SRT",
        path="canal-principal",
        role="READER",
        bitrate_bps=4_310_000,
        uptime_seconds=3_725,
        username="cliente-norte",
    )

    return ActiveConnectionsPanelData(
        captured_at=datetime(
            2026,
            7,
            27,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        connections=(connection,),
    )


def test_render_returns_panel() -> None:
    panel = ActiveConnectionsPanelRenderer().render(
        build_panel()
    )

    assert isinstance(panel, Panel)
    assert panel.title == "CONNECTED CLIENTS [1]"
    assert isinstance(panel.renderable, Table)


def test_render_contains_network_identity() -> None:
    panel = ActiveConnectionsPanelRenderer().render(
        build_panel()
    )

    table = panel.renderable

    assert isinstance(table, Table)

    headers = [
        column.header
        for column in table.columns
    ]

    assert "CLIENT" in headers
    assert "COUNTRY" in headers
    assert "ASN" in headers
    assert "PROVIDER" in headers
    assert "PROTOCOL" in headers
    assert "BITRATE" in headers

    row_text = " ".join(
        str(cell)
        for column in table.columns
        for cell in column._cells
    )

    assert "cliente-norte" in row_text
    assert "🇨🇷 CR" in row_text
    assert "AS17054" in row_text
    assert "RACSA" in row_text
    assert "SRT" in row_text
    assert "4.31 Mbps" in row_text


def test_render_uses_path_when_username_is_missing() -> None:
    connection = ActiveConnectionRow(
        remote_address="201.192.154.130:26676",
        country="Costa Rica",
        country_code="CR",
        asn=17054,
        provider="RACSA",
        protocol="SRT",
        path="canal-principal",
        role="READER",
        bitrate_bps=4_310_000,
        uptime_seconds=3_725,
        username=None,
    )

    panel = ActiveConnectionsPanelRenderer().render(
        ActiveConnectionsPanelData(
            captured_at=datetime.now(timezone.utc),
            connections=(connection,),
        )
    )

    table = panel.renderable

    assert isinstance(table, Table)

    row_text = " ".join(
        str(cell)
        for column in table.columns
        for cell in column._cells
    )

    assert "canal-principal" in row_text


def test_render_formats_missing_asn() -> None:
    assert (
        ActiveConnectionsPanelRenderer._format_asn(None)
        == "N/A"
    )


def test_render_formats_valid_asn() -> None:
    assert (
        ActiveConnectionsPanelRenderer._format_asn(17054)
        == "AS17054"
    )


def test_render_formats_country_code() -> None:
    assert (
        ActiveConnectionsPanelRenderer._format_country("CR")
        == "🇨🇷 CR"
    )


def test_render_normalizes_country_code() -> None:
    assert (
        ActiveConnectionsPanelRenderer._format_country("cr")
        == "🇨🇷 CR"
    )


def test_render_formats_missing_country_code() -> None:
    assert (
        ActiveConnectionsPanelRenderer._format_country(None)
        == "🌍 --"
    )


def test_render_rejects_invalid_country_code() -> None:
    assert (
        ActiveConnectionsPanelRenderer._format_country("CRI")
        == "🌍 --"
    )


def test_render_empty_panel() -> None:
    panel = ActiveConnectionsPanelRenderer().render(
        ActiveConnectionsPanelData.empty(
            captured_at=datetime.now(timezone.utc),
        )
    )

    assert isinstance(panel, Panel)
    assert panel.title == "CONNECTED CLIENTS"
    assert isinstance(panel.renderable, Text)
    assert "No hay clientes conectados." in str(
        panel.renderable
    )