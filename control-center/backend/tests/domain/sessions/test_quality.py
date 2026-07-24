"""Pruebas de evaluación de calidad de sesiones."""

import pytest

from app.domain.sessions import (
    SessionQuality,
    evaluate_session_quality,
)


@pytest.mark.parametrize(
    (
        "rtt_ms",
        "loss",
        "retransmission",
        "expected",
    ),
    [
        (None, None, None, SessionQuality.UNKNOWN),
        (5.0, 0.0, 0.0, SessionQuality.EXCELLENT),
        (30.0, 0.0, 0.0, SessionQuality.GOOD),
        (80.0, 0.0, 0.0, SessionQuality.FAIR),
        (150.0, 0.0, 0.0, SessionQuality.POOR),
        (250.0, 0.0, 0.0, SessionQuality.CRITICAL),
        (5.0, 0.25, 0.0, SessionQuality.GOOD),
        (5.0, 1.0, 0.0, SessionQuality.FAIR),
        (5.0, 2.0, 0.0, SessionQuality.POOR),
        (5.0, 5.0, 0.0, SessionQuality.CRITICAL),
        (5.0, 0.0, 0.5, SessionQuality.GOOD),
        (5.0, 0.0, 2.0, SessionQuality.FAIR),
        (5.0, 0.0, 5.0, SessionQuality.POOR),
        (5.0, 0.0, 10.0, SessionQuality.CRITICAL),
    ],
)
def test_evaluate_session_quality(
    rtt_ms: float | None,
    loss: float | None,
    retransmission: float | None,
    expected: SessionQuality,
) -> None:
    quality = evaluate_session_quality(
        rtt_ms=rtt_ms,
        packet_loss_rate=loss,
        retransmission_rate=retransmission,
    )

    assert quality is expected


def test_worst_metric_determines_quality() -> None:
    quality = evaluate_session_quality(
        rtt_ms=5.0,
        packet_loss_rate=0.0,
        retransmission_rate=10.0,
    )

    assert quality is SessionQuality.CRITICAL


@pytest.mark.parametrize(
    "field",
    [
        "rtt_ms",
        "packet_loss_rate",
        "retransmission_rate",
    ],
)
def test_negative_metrics_are_rejected(field: str) -> None:
    values = {
        "rtt_ms": 5.0,
        "packet_loss_rate": 0.0,
        "retransmission_rate": 0.0,
    }
    values[field] = -1.0

    with pytest.raises(ValueError):
        evaluate_session_quality(**values)
