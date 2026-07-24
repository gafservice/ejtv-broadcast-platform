"""Pruebas de modelos del dominio de sesiones."""

from datetime import UTC, datetime, timedelta

import pytest

from app.domain.sessions import (
    ActiveSession,
    SessionProtocol,
    SessionQuality,
    SessionRole,
    SessionSnapshot,
)


def build_session(
    *,
    session_id: str = "session-001",
    protocol: SessionProtocol = SessionProtocol.SRT,
    role: SessionRole = SessionRole.READER,
    remote_ip: str = "201.192.154.132",
    remote_port: int | None = 21520,
    connected_since: datetime | None = None,
) -> ActiveSession:
    """Construye una sesión válida para pruebas."""

    return ActiveSession(
        session_id=session_id,
        protocol=protocol,
        role=role,
        state="read",
        remote_ip=remote_ip,
        remote_port=remote_port,
        path="enlace",
        connected_since=(
            connected_since
            or datetime.now(UTC)
        ),
        bytes_sent=2_980_118_536,
        bitrate_send_mbps=3.97,
        link_capacity_mbps=20.53,
        rtt_ms=6.96,
        packets_sent=2_309_449,
        packets_lost=29_909,
        packets_retransmitted=23_026,
        quality=SessionQuality.EXCELLENT,
    )


def test_active_session_exposes_remote_address() -> None:
    session = build_session()

    assert session.remote_address == "201.192.154.132:21520"


def test_ipv6_remote_address_uses_brackets() -> None:
    session = build_session(
        remote_ip="2001:db8::10",
        remote_port=8890,
    )

    assert session.remote_address == "[2001:db8::10]:8890"


def test_reader_uses_send_bitrate() -> None:
    session = build_session()

    assert session.is_reader is True
    assert session.is_publisher is False
    assert session.effective_bitrate_mbps == 3.97


def test_publisher_uses_receive_bitrate() -> None:
    session = ActiveSession(
        session_id="publisher-001",
        protocol=SessionProtocol.SRT,
        role=SessionRole.PUBLISHER,
        state="publish",
        remote_ip="192.168.1.20",
        remote_port=55000,
        path="enlace",
        connected_since=datetime.now(UTC),
        bitrate_receive_mbps=4.5,
    )

    assert session.is_publisher is True
    assert session.effective_bitrate_mbps == 4.5


def test_duration_is_calculated_in_utc() -> None:
    connected_since = datetime(
        2026,
        7,
        24,
        12,
        0,
        tzinfo=UTC,
    )
    session = build_session(
        connected_since=connected_since,
    )

    now = connected_since + timedelta(
        hours=2,
        minutes=30,
    )

    assert session.duration_seconds(now=now) == 9_000.0


def test_duration_never_returns_negative_value() -> None:
    connected_since = datetime.now(UTC)
    session = build_session(
        connected_since=connected_since,
    )

    assert session.duration_seconds(
        now=connected_since - timedelta(seconds=10)
    ) == 0.0


@pytest.mark.parametrize(
    ("remote_ip", "expected"),
    [
        ("127.0.0.1", "Servidor local"),
        ("192.168.1.20", "Red local"),
        ("10.0.18.20", "Red local"),
        ("201.192.154.132", "Desconocido"),
    ],
)
def test_location_label_without_geoip(
    remote_ip: str,
    expected: str,
) -> None:
    session = build_session(
        remote_ip=remote_ip,
    )

    assert session.location_label == expected


def test_location_prefers_country_name() -> None:
    base = build_session()

    session = ActiveSession(
        session_id=base.session_id,
        protocol=base.protocol,
        role=base.role,
        state=base.state,
        remote_ip=base.remote_ip,
        remote_port=base.remote_port,
        path=base.path,
        connected_since=base.connected_since,
        country_code="CR",
        country_name="Costa Rica",
    )

    assert session.location_label == "Costa Rica"


@pytest.mark.parametrize(
    "invalid_ip",
    [
        "",
        "not-an-ip",
        "999.999.999.999",
    ],
)
def test_invalid_remote_ip_is_rejected(
    invalid_ip: str,
) -> None:
    with pytest.raises(ValueError):
        build_session(remote_ip=invalid_ip)


@pytest.mark.parametrize(
    "remote_port",
    [
        0,
        -1,
        65_536,
    ],
)
def test_invalid_remote_port_is_rejected(
    remote_port: int,
) -> None:
    with pytest.raises(ValueError):
        build_session(remote_port=remote_port)


def test_naive_connected_since_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_session(
            connected_since=datetime(2026, 7, 24, 12, 0)
        )


def test_snapshot_calculates_totals() -> None:
    reader = build_session(
        session_id="reader-001",
    )
    publisher = build_session(
        session_id="publisher-001",
        protocol=SessionProtocol.RTMP,
        role=SessionRole.PUBLISHER,
    )

    snapshot = SessionSnapshot(
        captured_at=datetime.now(UTC),
        sessions=(reader, publisher),
    )

    assert snapshot.session_count == 2
    assert snapshot.reader_count == 1
    assert snapshot.publisher_count == 1
    assert snapshot.protocols == (
        SessionProtocol.RTMP,
        SessionProtocol.SRT,
    )
    assert snapshot.get_session("reader-001") is reader
    assert snapshot.get_session("missing") is None


def test_snapshot_rejects_duplicate_identifiers() -> None:
    first = build_session()
    duplicate = build_session()

    with pytest.raises(ValueError):
        SessionSnapshot(
            captured_at=datetime.now(UTC),
            sessions=(first, duplicate),
        )


def test_empty_snapshot_is_valid() -> None:
    snapshot = SessionSnapshot.empty()

    assert snapshot.session_count == 0
    assert snapshot.reader_count == 0
    assert snapshot.publisher_count == 0
    assert snapshot.protocols == ()
