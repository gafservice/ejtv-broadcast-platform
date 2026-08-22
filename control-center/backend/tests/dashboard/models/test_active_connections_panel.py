"""Pruebas de los modelos del panel CONNECTED CLIENTS."""

from datetime import datetime, timezone

import pytest

from app.dashboard.models import (
    ActiveConnectionRow,
    ActiveConnectionsPanelData,
)


def build_connection() -> ActiveConnectionRow:
    """Construye una conexión válida para las pruebas."""

    return ActiveConnectionRow(
        session_id="session-001",
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


def test_active_connection_row_stores_expected_values() -> None:
    connection = build_connection()

    assert connection.remote_address == "201.192.154.130:26676"
    assert connection.country == "Costa Rica"
    assert connection.protocol == "SRT"
    assert connection.path == "canal-principal"
    assert connection.role == "READER"
    assert connection.bitrate_bps == 4_310_000
    assert connection.uptime_seconds == 3_725
    assert connection.username is None
    assert connection.asn == 17054
    assert connection.provider == "RACSA"


def test_active_connection_row_accepts_username() -> None:
    connection = ActiveConnectionRow(
        session_id="session-username",
        remote_address="190.115.202.229:46876",
        country="Costa Rica",
        country_code="CR",
        protocol="SRT",
        path="enlace",
        role="READER",
        bitrate_bps=4_390_000,
        uptime_seconds=500,
        username="cliente-norte",
        asn=17054,
        provider="RACSA",
    )

    assert connection.username == "cliente-norte"


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("remote_address", "   "),
        ("country", ""),
        ("protocol", " "),
        ("path", ""),
        ("role", "   "),
    ),
)
def test_active_connection_row_rejects_empty_text(
    field_name: str,
    value: str,
) -> None:
    values = {
        "session_id": "session-parametrized",
        "remote_address": "201.192.154.130:26676",
        "country": "Costa Rica",
        "country_code": "CR",
        "asn": 17054,
        "provider": "RACSA",
        "protocol": "SRT",
        "path": "canal-principal",
        "role": "READER",
    }
    values[field_name] = value

    with pytest.raises(ValueError):
        ActiveConnectionRow(
            **values,
            bitrate_bps=4_310_000,
            uptime_seconds=100,
        )


def test_active_connection_row_rejects_negative_bitrate() -> None:
    with pytest.raises(ValueError):
        ActiveConnectionRow(
            session_id="session-validation",
            remote_address="201.192.154.130:26676",
            country="Costa Rica",
            country_code="CR",
            asn=17054,
            provider="RACSA",
            protocol="SRT",
            path="canal-principal",
            role="READER",
            bitrate_bps=-1,
            uptime_seconds=100,
        )


def test_active_connection_row_rejects_negative_uptime() -> None:
    with pytest.raises(ValueError):
        ActiveConnectionRow(
            session_id="session-validation",
            remote_address="201.192.154.130:26676",
            country="Costa Rica",
            country_code="CR",
            asn=17054,
            provider="RACSA",
            protocol="SRT",
            path="canal-principal",
            role="READER",
            bitrate_bps=4_310_000,
            uptime_seconds=-1,
        )


def test_active_connections_panel_stores_connections() -> None:
    captured_at = datetime(
        2026,
        7,
        26,
        18,
        0,
        tzinfo=timezone.utc,
    )
    connection = build_connection()

    panel = ActiveConnectionsPanelData(
        captured_at=captured_at,
        connections=(connection,),
    )

    assert panel.captured_at == captured_at
    assert panel.connections == (connection,)
    assert panel.connection_count == 1


def test_active_connections_panel_accepts_empty_connections() -> None:
    captured_at = datetime(
        2026,
        7,
        26,
        18,
        0,
        tzinfo=timezone.utc,
    )

    panel = ActiveConnectionsPanelData.empty(
        captured_at=captured_at,
    )

    assert panel.connections == ()
    assert panel.connection_count == 0


def test_active_connections_panel_rejects_naive_datetime() -> None:
    with pytest.raises(ValueError):
        ActiveConnectionsPanelData(
            captured_at=datetime(2026, 7, 26, 18, 0),
            connections=(),
        )


def test_active_connections_panel_accepts_duplicate_remote_addresses() -> None:
    first = build_connection()

    second = ActiveConnectionRow(
        session_id="session-002",
        remote_address=first.remote_address,
        country=first.country,
        country_code=first.country_code,
        asn=first.asn,
        provider=first.provider,
        protocol="HLS",
        path="ejtv",
        role="READER",
        bitrate_bps=2_000_000,
        uptime_seconds=120,
        username=None,
    )

    panel = ActiveConnectionsPanelData(
        captured_at=datetime(
            2026,
            7,
            26,
            18,
            0,
            tzinfo=timezone.utc,
        ),
        connections=(first, second),
    )

    assert panel.connection_count == 2
    assert (
        panel.connections[0].remote_address
        == panel.connections[1].remote_address
    )
    assert (
        panel.connections[0].session_id
        != panel.connections[1].session_id
    )


def test_active_connections_panel_rejects_duplicate_session_ids() -> None:
    connection = build_connection()

    with pytest.raises(
        ValueError,
        match="session_id",
    ):
        ActiveConnectionsPanelData(
            captured_at=datetime(
                2026,
                7,
                26,
                18,
                0,
                tzinfo=timezone.utc,
            ),
            connections=(connection, connection),
        )
