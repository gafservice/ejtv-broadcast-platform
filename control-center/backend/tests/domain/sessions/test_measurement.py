"""Pruebas para mediciones derivadas de sesiones."""

from datetime import UTC, datetime

import pytest

from app.domain.sessions import (
    ActiveSession,
    SessionMeasurement,
    SessionPathSummary,
    SessionProtocol,
    SessionQuality,
    SessionRole,
)


CAPTURED_AT = datetime(2026, 7, 24, 20, 0, tzinfo=UTC)
CONNECTED_AT = datetime(2026, 7, 24, 19, 0, tzinfo=UTC)


def build_session(
    *,
    session_id: str = "session-1",
    role: SessionRole = SessionRole.READER,
    quality: SessionQuality = SessionQuality.EXCELLENT,
    path: str | None = "channel-1",
) -> ActiveSession:
    """Construye una sesión válida para pruebas."""

    return ActiveSession(
        session_id=session_id,
        protocol=SessionProtocol.SRT,
        role=role,
        state="read",
        remote_ip="203.0.113.10",
        remote_port=9000,
        path=path,
        connected_since=CONNECTED_AT,
        bitrate_receive_mbps=1.5,
        bitrate_send_mbps=4.0,
        quality=quality,
    )


def build_path_summary() -> SessionPathSummary:
    """Construye un resumen de path válido."""

    return SessionPathSummary(
        path="channel-1",
        session_count=1,
        reader_count=1,
        publisher_count=0,
        inbound_bitrate_mbps=0.0,
        outbound_bitrate_mbps=4.0,
        degraded_session_count=0,
        worst_quality=SessionQuality.EXCELLENT,
    )


def build_measurement(
    *,
    sessions: tuple[ActiveSession, ...] | None = None,
    paths: tuple[SessionPathSummary, ...] | None = None,
    total_sessions: int = 1,
    reader_count: int = 1,
    publisher_count: int = 0,
    unknown_role_count: int = 0,
    degraded_session_count: int = 0,
    critical_session_count: int = 0,
) -> SessionMeasurement:
    """Construye una medición válida para pruebas."""

    return SessionMeasurement(
        captured_at=CAPTURED_AT,
        sessions=sessions or (build_session(),),
        paths=paths or (build_path_summary(),),
        total_sessions=total_sessions,
        reader_count=reader_count,
        publisher_count=publisher_count,
        unknown_role_count=unknown_role_count,
        degraded_session_count=degraded_session_count,
        critical_session_count=critical_session_count,
        total_inbound_bitrate_mbps=0.0,
        total_outbound_bitrate_mbps=4.0,
        worst_quality=SessionQuality.EXCELLENT,
        protocols=(SessionProtocol.SRT,),
    )


def test_path_summary_accepts_valid_values() -> None:
    summary = build_path_summary()

    assert summary.path == "channel-1"
    assert summary.session_count == 1
    assert summary.reader_count == 1
    assert summary.worst_quality is SessionQuality.EXCELLENT


@pytest.mark.parametrize(
    "field_name",
    [
        "session_count",
        "reader_count",
        "publisher_count",
        "degraded_session_count",
    ],
)
def test_path_summary_rejects_negative_counters(
    field_name: str,
) -> None:
    values = {
        "path": "channel-1",
        "session_count": 1,
        "reader_count": 1,
        "publisher_count": 0,
        "inbound_bitrate_mbps": 0.0,
        "outbound_bitrate_mbps": 4.0,
        "degraded_session_count": 0,
        "worst_quality": SessionQuality.EXCELLENT,
    }
    values[field_name] = -1

    with pytest.raises(ValueError):
        SessionPathSummary(**values)


def test_path_summary_rejects_empty_path() -> None:
    with pytest.raises(ValueError, match="path no puede estar vacío"):
        SessionPathSummary(
            path=" ",
            session_count=0,
            reader_count=0,
            publisher_count=0,
            inbound_bitrate_mbps=0.0,
            outbound_bitrate_mbps=0.0,
            degraded_session_count=0,
            worst_quality=SessionQuality.UNKNOWN,
        )


def test_path_summary_rejects_role_count_above_total() -> None:
    with pytest.raises(ValueError):
        SessionPathSummary(
            path="channel-1",
            session_count=1,
            reader_count=1,
            publisher_count=1,
            inbound_bitrate_mbps=0.0,
            outbound_bitrate_mbps=0.0,
            degraded_session_count=0,
            worst_quality=SessionQuality.UNKNOWN,
        )


def test_measurement_accepts_valid_values() -> None:
    measurement = build_measurement()

    assert measurement.total_sessions == 1
    assert measurement.reader_count == 1
    assert measurement.publisher_count == 0
    assert measurement.protocols == (SessionProtocol.SRT,)


def test_measurement_reports_degraded_sessions() -> None:
    degraded = build_session(
        quality=SessionQuality.FAIR,
    )

    measurement = SessionMeasurement(
        captured_at=CAPTURED_AT,
        sessions=(degraded,),
        paths=(
            SessionPathSummary(
                path="channel-1",
                session_count=1,
                reader_count=1,
                publisher_count=0,
                inbound_bitrate_mbps=0.0,
                outbound_bitrate_mbps=4.0,
                degraded_session_count=1,
                worst_quality=SessionQuality.FAIR,
            ),
        ),
        total_sessions=1,
        reader_count=1,
        publisher_count=0,
        unknown_role_count=0,
        degraded_session_count=1,
        critical_session_count=0,
        total_inbound_bitrate_mbps=0.0,
        total_outbound_bitrate_mbps=4.0,
        worst_quality=SessionQuality.FAIR,
        protocols=(SessionProtocol.SRT,),
    )

    assert measurement.has_degraded_sessions is True
    assert measurement.has_critical_sessions is False


def test_measurement_reports_critical_sessions() -> None:
    critical = build_session(
        quality=SessionQuality.CRITICAL,
    )

    measurement = SessionMeasurement(
        captured_at=CAPTURED_AT,
        sessions=(critical,),
        paths=(
            SessionPathSummary(
                path="channel-1",
                session_count=1,
                reader_count=1,
                publisher_count=0,
                inbound_bitrate_mbps=0.0,
                outbound_bitrate_mbps=4.0,
                degraded_session_count=1,
                worst_quality=SessionQuality.CRITICAL,
            ),
        ),
        total_sessions=1,
        reader_count=1,
        publisher_count=0,
        unknown_role_count=0,
        degraded_session_count=1,
        critical_session_count=1,
        total_inbound_bitrate_mbps=0.0,
        total_outbound_bitrate_mbps=4.0,
        worst_quality=SessionQuality.CRITICAL,
        protocols=(SessionProtocol.SRT,),
    )

    assert measurement.has_degraded_sessions is True
    assert measurement.has_critical_sessions is True


def test_measurement_rejects_naive_datetime() -> None:
    with pytest.raises(ValueError, match="zona horaria"):
        SessionMeasurement(
            captured_at=datetime(2026, 7, 24, 20, 0),
            sessions=(),
            paths=(),
            total_sessions=0,
            reader_count=0,
            publisher_count=0,
            unknown_role_count=0,
            degraded_session_count=0,
            critical_session_count=0,
            total_inbound_bitrate_mbps=0.0,
            total_outbound_bitrate_mbps=0.0,
            worst_quality=SessionQuality.UNKNOWN,
            protocols=(),
        )


def test_measurement_rejects_total_mismatch() -> None:
    with pytest.raises(ValueError, match="total_sessions"):
        build_measurement(total_sessions=2)


def test_measurement_rejects_role_count_mismatch() -> None:
    with pytest.raises(ValueError, match="suma de roles"):
        build_measurement(
            reader_count=0,
            publisher_count=0,
            unknown_role_count=0,
        )


def test_measurement_rejects_critical_above_degraded() -> None:
    with pytest.raises(ValueError, match="critical_session_count"):
        build_measurement(
            degraded_session_count=0,
            critical_session_count=1,
        )


def test_measurement_rejects_duplicate_session_ids() -> None:
    session = build_session()

    with pytest.raises(ValueError, match="session_id duplicados"):
        build_measurement(
            sessions=(session, session),
            total_sessions=2,
            reader_count=2,
        )


def test_measurement_rejects_duplicate_paths() -> None:
    path = build_path_summary()

    with pytest.raises(ValueError, match="paths duplicados"):
        build_measurement(
            paths=(path, path),
        )


@pytest.mark.parametrize(
    "field_name",
    [
        "total_inbound_bitrate_mbps",
        "total_outbound_bitrate_mbps",
    ],
)
def test_measurement_rejects_negative_bitrate(
    field_name: str,
) -> None:
    values = {
        "captured_at": CAPTURED_AT,
        "sessions": (build_session(),),
        "paths": (build_path_summary(),),
        "total_sessions": 1,
        "reader_count": 1,
        "publisher_count": 0,
        "unknown_role_count": 0,
        "degraded_session_count": 0,
        "critical_session_count": 0,
        "total_inbound_bitrate_mbps": 0.0,
        "total_outbound_bitrate_mbps": 4.0,
        "worst_quality": SessionQuality.EXCELLENT,
        "protocols": (SessionProtocol.SRT,),
    }
    values[field_name] = -1.0

    with pytest.raises(ValueError):
        SessionMeasurement(**values)
