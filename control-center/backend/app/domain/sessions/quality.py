"""Evaluación de calidad para sesiones multimedia."""

from __future__ import annotations

from enum import StrEnum


class SessionQuality(StrEnum):
    """Calidad técnica normalizada de una sesión."""

    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    FAIR = "FAIR"
    POOR = "POOR"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


def evaluate_session_quality(
    *,
    rtt_ms: float | None,
    packet_loss_rate: float | None,
    retransmission_rate: float | None,
) -> SessionQuality:
    """Evalúa la calidad técnica de una sesión.

    Los valores de pérdida y retransmisión se expresan como porcentaje:

    - 0.5 representa 0.5 %
    - 1.0 representa 1 %
    - 5.0 representa 5 %

    La evaluación utiliza el peor resultado entre RTT, pérdida y
    retransmisiones.
    """

    available_values = (
        rtt_ms,
        packet_loss_rate,
        retransmission_rate,
    )

    if all(value is None for value in available_values):
        return SessionQuality.UNKNOWN

    normalized_rtt = _normalize_non_negative(rtt_ms)
    normalized_loss = _normalize_non_negative(packet_loss_rate)
    normalized_retransmission = _normalize_non_negative(
        retransmission_rate
    )

    if (
        _at_least(normalized_rtt, 250.0)
        or _at_least(normalized_loss, 5.0)
        or _at_least(normalized_retransmission, 10.0)
    ):
        return SessionQuality.CRITICAL

    if (
        _at_least(normalized_rtt, 150.0)
        or _at_least(normalized_loss, 2.0)
        or _at_least(normalized_retransmission, 5.0)
    ):
        return SessionQuality.POOR

    if (
        _at_least(normalized_rtt, 80.0)
        or _at_least(normalized_loss, 1.0)
        or _at_least(normalized_retransmission, 2.0)
    ):
        return SessionQuality.FAIR

    if (
        _at_least(normalized_rtt, 30.0)
        or _at_least(normalized_loss, 0.25)
        or _at_least(normalized_retransmission, 0.5)
    ):
        return SessionQuality.GOOD

    return SessionQuality.EXCELLENT


def _normalize_non_negative(value: float | None) -> float | None:
    """Normaliza una métrica opcional y rechaza valores negativos."""

    if value is None:
        return None

    numeric_value = float(value)

    if numeric_value < 0:
        raise ValueError("Las métricas de calidad no pueden ser negativas.")

    return numeric_value


def _at_least(value: float | None, threshold: float) -> bool:
    """Indica si un valor disponible alcanza un umbral."""

    return value is not None and value >= threshold
