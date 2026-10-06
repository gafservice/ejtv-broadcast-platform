"""Contract tests for aggregate Signal Health.

ENG-013C — Signal Health Contract v1

Signal Health combines already-evaluated Media Health and Transport
Service Health for one logical multimedia signal.

Architectural boundary:

- Signal Health does not inspect codecs, GOP, PCR, MPEG-TS, packets,
  sessions or protocol metrics directly.
- Media-specific evidence belongs to Media Health.
- Transport/session evidence belongs to Service Health.
- Signal Health combines those conclusions without inventing evidence.
"""

from __future__ import annotations

import pytest

from app.domain.streaming.source_transport_health import (
    SourceTransportHealth,
)
from app.domain.streaming.health import HealthStatus
from app.domain.streaming.media_health import MediaHealth
from app.domain.streaming.signal_health import (
    SignalHealth,
    SignalHealthEvaluator,
)


def media_health(
    status: HealthStatus,
    *,
    profile_id: str = "profile-main",
    service_id: str = "service-a",
    path_name: str | None = "service-a",
) -> MediaHealth:
    return MediaHealth(
        profile_id=profile_id,
        service_id=service_id,
        path_name=path_name,
        status=status,
    )


def transport_health(
    status: HealthStatus,
    *,
    service_id: str = "service-a",
    path_name: str = "service-a",
    source_type: str = "srtSource",
) -> SourceTransportHealth:
    return SourceTransportHealth(
        service_id=service_id,
        path_name=path_name,
        source_type=source_type,
        status=status,
    )


@pytest.mark.parametrize(
    ("media_status", "transport_status", "expected"),
    (
        (
            HealthStatus.HEALTHY,
            HealthStatus.HEALTHY,
            HealthStatus.HEALTHY,
        ),
        (
            HealthStatus.HEALTHY,
            HealthStatus.DEGRADED,
            HealthStatus.DEGRADED,
        ),
        (
            HealthStatus.HEALTHY,
            HealthStatus.CRITICAL,
            HealthStatus.CRITICAL,
        ),
        (
            HealthStatus.DEGRADED,
            HealthStatus.HEALTHY,
            HealthStatus.DEGRADED,
        ),
        (
            HealthStatus.DEGRADED,
            HealthStatus.DEGRADED,
            HealthStatus.DEGRADED,
        ),
        (
            HealthStatus.DEGRADED,
            HealthStatus.CRITICAL,
            HealthStatus.CRITICAL,
        ),
        (
            HealthStatus.CRITICAL,
            HealthStatus.HEALTHY,
            HealthStatus.CRITICAL,
        ),
        (
            HealthStatus.CRITICAL,
            HealthStatus.DEGRADED,
            HealthStatus.CRITICAL,
        ),
        (
            HealthStatus.CRITICAL,
            HealthStatus.CRITICAL,
            HealthStatus.CRITICAL,
        ),
        (
            HealthStatus.UNKNOWN,
            HealthStatus.HEALTHY,
            HealthStatus.UNKNOWN,
        ),
        (
            HealthStatus.HEALTHY,
            HealthStatus.UNKNOWN,
            HealthStatus.UNKNOWN,
        ),
        (
            HealthStatus.UNKNOWN,
            HealthStatus.DEGRADED,
            HealthStatus.DEGRADED,
        ),
        (
            HealthStatus.DEGRADED,
            HealthStatus.UNKNOWN,
            HealthStatus.DEGRADED,
        ),
        (
            HealthStatus.UNKNOWN,
            HealthStatus.CRITICAL,
            HealthStatus.CRITICAL,
        ),
        (
            HealthStatus.CRITICAL,
            HealthStatus.UNKNOWN,
            HealthStatus.CRITICAL,
        ),
        (
            HealthStatus.UNKNOWN,
            HealthStatus.UNKNOWN,
            HealthStatus.UNKNOWN,
        ),
    ),
)
def test_signal_health_status_matrix(
    media_status: HealthStatus,
    transport_status: HealthStatus,
    expected: HealthStatus,
) -> None:
    result = SignalHealthEvaluator().evaluate(
        media_health=media_health(media_status),
        transport_health=transport_health(transport_status),
    )

    assert result.status is expected


def test_signal_health_preserves_signal_identity() -> None:
    result = SignalHealthEvaluator().evaluate(
        media_health=media_health(
            HealthStatus.HEALTHY,
            profile_id="generic-profile",
            service_id="generic-service",
            path_name="generic-path",
        ),
        transport_health=transport_health(
            HealthStatus.HEALTHY,
            service_id="generic-service",
        ),
    )

    assert result.profile_id == "generic-profile"
    assert result.service_id == "generic-service"
    assert result.path_name == "generic-path"


def test_signal_health_preserves_input_health_conclusions() -> None:
    media = media_health(HealthStatus.DEGRADED)
    transport = transport_health(HealthStatus.HEALTHY)

    result = SignalHealthEvaluator().evaluate(
        media_health=media,
        transport_health=transport,
    )

    assert result.media_status is HealthStatus.DEGRADED
    assert result.transport_status is HealthStatus.HEALTHY
    assert result.status is HealthStatus.DEGRADED


def test_signal_health_rejects_mismatched_service_identity() -> None:
    with pytest.raises(
        ValueError,
        match="service",
    ):
        SignalHealthEvaluator().evaluate(
            media_health=media_health(
                HealthStatus.HEALTHY,
                service_id="service-a",
            ),
            transport_health=transport_health(
                HealthStatus.HEALTHY,
                service_id="service-b",
            ),
        )


def test_signal_health_reuses_canonical_health_status() -> None:
    result = SignalHealth(
        profile_id="profile-main",
        service_id="service-a",
        path_name="service-a",
        media_status=HealthStatus.HEALTHY,
        transport_status=HealthStatus.HEALTHY,
        status=HealthStatus.HEALTHY,
    )

    assert result.status is HealthStatus.HEALTHY
    assert result.media_status is HealthStatus.HEALTHY
    assert result.transport_status is HealthStatus.HEALTHY


def test_signal_health_normalizes_identity() -> None:
    result = SignalHealth(
        profile_id="  profile-main  ",
        service_id="  service-a  ",
        path_name="  service-a  ",
        media_status=HealthStatus.HEALTHY,
        transport_status=HealthStatus.HEALTHY,
        status=HealthStatus.HEALTHY,
    )

    assert result.profile_id == "profile-main"
    assert result.service_id == "service-a"
    assert result.path_name == "service-a"


@pytest.mark.parametrize(
    ("kwargs", "exception", "message"),
    (
        (
            {
                "profile_id": " ",
                "service_id": "service-a",
                "path_name": "service-a",
                "media_status": HealthStatus.HEALTHY,
                "transport_status": HealthStatus.HEALTHY,
                "status": HealthStatus.HEALTHY,
            },
            ValueError,
            "profile_id",
        ),
        (
            {
                "profile_id": "profile-main",
                "service_id": " ",
                "path_name": "service-a",
                "media_status": HealthStatus.HEALTHY,
                "transport_status": HealthStatus.HEALTHY,
                "status": HealthStatus.HEALTHY,
            },
            ValueError,
            "service_id",
        ),
        (
            {
                "profile_id": "profile-main",
                "service_id": "service-a",
                "path_name": " ",
                "media_status": HealthStatus.HEALTHY,
                "transport_status": HealthStatus.HEALTHY,
                "status": HealthStatus.HEALTHY,
            },
            ValueError,
            "path_name",
        ),
        (
            {
                "profile_id": "profile-main",
                "service_id": "service-a",
                "path_name": "service-a",
                "media_status": "HEALTHY",
                "transport_status": HealthStatus.HEALTHY,
                "status": HealthStatus.HEALTHY,
            },
            TypeError,
            "media_status",
        ),
        (
            {
                "profile_id": "profile-main",
                "service_id": "service-a",
                "path_name": "service-a",
                "media_status": HealthStatus.HEALTHY,
                "transport_status": "HEALTHY",
                "status": HealthStatus.HEALTHY,
            },
            TypeError,
            "transport_status",
        ),
        (
            {
                "profile_id": "profile-main",
                "service_id": "service-a",
                "path_name": "service-a",
                "media_status": HealthStatus.HEALTHY,
                "transport_status": HealthStatus.HEALTHY,
                "status": "HEALTHY",
            },
            TypeError,
            "status",
        ),
    ),
)
def test_signal_health_rejects_invalid_values(
    kwargs,
    exception,
    message,
) -> None:
    with pytest.raises(exception, match=message):
        SignalHealth(**kwargs)


def test_signal_health_evaluator_rejects_wrong_media_type() -> None:
    with pytest.raises(TypeError, match="MediaHealth"):
        SignalHealthEvaluator().evaluate(
            media_health=object(),
            transport_health=transport_health(
                HealthStatus.HEALTHY
            ),
        )


def test_signal_health_evaluator_rejects_wrong_transport_type() -> None:
    with pytest.raises(TypeError, match="SourceTransportHealth"):
        SignalHealthEvaluator().evaluate(
            media_health=media_health(
                HealthStatus.HEALTHY
            ),
            transport_health=object(),
        )
def test_evaluator_accepts_effective_unknown_media_status() -> None:
    """Freshness UNKNOWN must not require a synthetic MediaHealth."""

    transport = transport_health(
        HealthStatus.HEALTHY,
        service_id="impact",
        path_name="impact"
    )

    result = SignalHealthEvaluator().evaluate(
        profile_id="impact-main",
        service_id="impact",
        path_name="impact",
        media_status=HealthStatus.UNKNOWN,
        transport_health=transport,
    )

    assert result.profile_id == "impact-main"
    assert result.service_id == "impact"
    assert result.path_name == "impact"
    assert result.media_status is HealthStatus.UNKNOWN
    assert result.transport_status is HealthStatus.HEALTHY
    assert result.status is HealthStatus.UNKNOWN


def test_evaluator_known_negative_transport_dominates_unknown_media() -> None:
    """UNKNOWN Media must not hide current negative transport evidence."""

    transport = transport_health(
        HealthStatus.CRITICAL,
        service_id="impact",
        path_name="impact"
    )

    result = SignalHealthEvaluator().evaluate(
        profile_id="impact-main",
        service_id="impact",
        path_name="impact",
        media_status=HealthStatus.UNKNOWN,
        transport_health=transport,
    )

    assert result.media_status is HealthStatus.UNKNOWN
    assert result.transport_status is HealthStatus.CRITICAL
    assert result.status is HealthStatus.CRITICAL


def test_evaluator_rejects_non_health_status_media_status() -> None:
    transport = transport_health(
        HealthStatus.HEALTHY
    )

    with pytest.raises(TypeError):
        SignalHealthEvaluator().evaluate(
            profile_id="impact-main",
            service_id="impact",
            path_name="impact",
            media_status="UNKNOWN",  # type: ignore[arg-type]
            transport_health=transport,
        )


def test_evaluator_rejects_transport_service_identity_mismatch() -> None:
    transport = SourceTransportHealth(
        service_id="other-service",
        path_name="impact",
        source_type="srtSource",
        status=HealthStatus.HEALTHY,
    )

    with pytest.raises(
        ValueError,
        match="service",
    ):
        SignalHealthEvaluator().evaluate(
            profile_id="impact-main",
            service_id="impact",
            path_name="impact",
            media_status=HealthStatus.HEALTHY,
            transport_health=transport,
        )


def test_evaluator_rejects_transport_path_identity_mismatch() -> None:
    transport = SourceTransportHealth(
        service_id="impact",
        path_name="other-path",
        source_type="srtSource",
        status=HealthStatus.HEALTHY,
    )

    with pytest.raises(
        ValueError,
        match="path",
    ):
        SignalHealthEvaluator().evaluate(
            profile_id="impact-main",
            service_id="impact",
            path_name="impact",
            media_status=HealthStatus.HEALTHY,
            transport_health=transport,
        )

def test_signal_health_accepts_optional_reason() -> None:
    result = SignalHealth(
        profile_id="profile-main",
        service_id="service-a",
        path_name="service-a",
        media_status=HealthStatus.DEGRADED,
        transport_status=HealthStatus.HEALTHY,
        status=HealthStatus.DEGRADED,
        reason="media degraded",
    )

    assert result.reason == "media degraded"


def test_signal_health_reason_defaults_to_none() -> None:
    result = SignalHealth(
        profile_id="profile-main",
        service_id="service-a",
        path_name="service-a",
        media_status=HealthStatus.HEALTHY,
        transport_status=HealthStatus.HEALTHY,
        status=HealthStatus.HEALTHY,
    )

    assert result.reason is None


def test_evaluator_reason_is_none_when_signal_is_healthy() -> None:
    result = SignalHealthEvaluator().evaluate(
        profile_id="profile-main",
        service_id="service-a",
        path_name="service-a",
        media_status=HealthStatus.HEALTHY,
        transport_health=SourceTransportHealth(
            service_id="service-a",
            source_type="srtSource",
            path_name="service-a",
            status=HealthStatus.HEALTHY,
        ),
    )

    assert result.status is HealthStatus.HEALTHY
    assert result.reason is None


def test_evaluator_reason_identifies_media_degraded() -> None:
    result = SignalHealthEvaluator().evaluate(
        profile_id="profile-main",
        service_id="service-a",
        path_name="service-a",
        media_status=HealthStatus.DEGRADED,
        transport_health=SourceTransportHealth(
            service_id="service-a",
            source_type="srtSource",
            path_name="service-a",
            status=HealthStatus.HEALTHY,
        ),
    )

    assert result.status is HealthStatus.DEGRADED
    assert result.reason == "media degraded"


def test_evaluator_reason_identifies_transport_degraded() -> None:
    result = SignalHealthEvaluator().evaluate(
        profile_id="profile-main",
        service_id="service-a",
        path_name="service-a",
        media_status=HealthStatus.HEALTHY,
        transport_health=SourceTransportHealth(
            service_id="service-a",
            source_type="srtSource",
            path_name="service-a",
            status=HealthStatus.DEGRADED,
        ),
    )

    assert result.status is HealthStatus.DEGRADED
    assert result.reason == "transport degraded"


def test_evaluator_reason_identifies_transport_critical() -> None:
    result = SignalHealthEvaluator().evaluate(
        profile_id="profile-main",
        service_id="service-a",
        path_name="service-a",
        media_status=HealthStatus.HEALTHY,
        transport_health=SourceTransportHealth(
            service_id="service-a",
            source_type="srtSource",
            path_name="service-a",
            status=HealthStatus.CRITICAL,
        ),
    )

    assert result.status is HealthStatus.CRITICAL
    assert result.reason == "transport critical"


def test_evaluator_reason_identifies_media_unknown() -> None:
    result = SignalHealthEvaluator().evaluate(
        profile_id="profile-main",
        service_id="service-a",
        path_name="service-a",
        media_status=HealthStatus.UNKNOWN,
        transport_health=SourceTransportHealth(
            service_id="service-a",
            source_type="srtSource",
            path_name="service-a",
            status=HealthStatus.HEALTHY,
        ),
    )

    assert result.status is HealthStatus.UNKNOWN
    assert result.reason == "media unknown"


def test_evaluator_reason_identifies_transport_unknown() -> None:
    result = SignalHealthEvaluator().evaluate(
        profile_id="profile-main",
        service_id="service-a",
        path_name="service-a",
        media_status=HealthStatus.HEALTHY,
        transport_health=SourceTransportHealth(
            service_id="service-a",
            source_type="srtSource",
            path_name="service-a",
            status=HealthStatus.UNKNOWN,
        ),
    )

    assert result.status is HealthStatus.UNKNOWN
    assert result.reason == "transport unknown"


def test_evaluator_reason_preserves_both_equal_degraded_domains() -> None:
    result = SignalHealthEvaluator().evaluate(
        profile_id="profile-main",
        service_id="service-a",
        path_name="service-a",
        media_status=HealthStatus.DEGRADED,
        transport_health=SourceTransportHealth(
            service_id="service-a",
            source_type="srtSource",
            path_name="service-a",
            status=HealthStatus.DEGRADED,
        ),
    )

    assert result.status is HealthStatus.DEGRADED
    assert result.reason == "media degraded; transport degraded"


def test_evaluator_reason_reports_only_status_determining_domain() -> None:
    result = SignalHealthEvaluator().evaluate(
        profile_id="profile-main",
        service_id="service-a",
        path_name="service-a",
        media_status=HealthStatus.DEGRADED,
        transport_health=SourceTransportHealth(
            service_id="service-a",
            source_type="srtSource",
            path_name="service-a",
            status=HealthStatus.UNKNOWN,
        ),
    )

    assert result.status is HealthStatus.DEGRADED
    assert result.reason == "media degraded"


def test_signal_uses_detailed_transport_reason_when_transport_determines_degraded_status() -> None:
    evaluator = SignalHealthEvaluator()

    media_health = MediaHealth(
        profile_id="future-profile",
        service_id="future-service",
        path_name="future-path",
        status=HealthStatus.HEALTHY,
    )
    transport_health = SourceTransportHealth(
        service_id="future-service",
        path_name="future-path",
        source_type="futureSource",
        status=HealthStatus.DEGRADED,
        reason="no traffic",
    )

    result = evaluator.evaluate(
        media_health=media_health,
        transport_health=transport_health,
    )

    assert result.status is HealthStatus.DEGRADED
    assert result.reason == "no traffic"


def test_signal_uses_detailed_transport_reason_when_transport_determines_critical_status() -> None:
    evaluator = SignalHealthEvaluator()

    media_health = MediaHealth(
        profile_id="future-profile",
        service_id="future-service",
        path_name="future-path",
        status=HealthStatus.HEALTHY,
    )
    transport_health = SourceTransportHealth(
        service_id="future-service",
        path_name="future-path",
        source_type="futureSource",
        status=HealthStatus.CRITICAL,
        reason="source offline",
    )

    result = evaluator.evaluate(
        media_health=media_health,
        transport_health=transport_health,
    )

    assert result.status is HealthStatus.CRITICAL
    assert result.reason == "source offline"


def test_signal_uses_detailed_transport_reason_for_unknown_transport() -> None:
    evaluator = SignalHealthEvaluator()

    media_health = MediaHealth(
        profile_id="future-profile",
        service_id="future-service",
        path_name="future-path",
        status=HealthStatus.HEALTHY,
    )
    transport_health = SourceTransportHealth(
        service_id="future-service",
        path_name="future-path",
        source_type="futureSource",
        status=HealthStatus.UNKNOWN,
        reason="telemetry unavailable",
    )

    result = evaluator.evaluate(
        media_health=media_health,
        transport_health=transport_health,
    )

    assert result.status is HealthStatus.UNKNOWN
    assert result.reason == "telemetry unavailable"


def test_transport_reason_does_not_override_more_severe_media_reason() -> None:
    evaluator = SignalHealthEvaluator()

    media_health = MediaHealth(
        profile_id="future-profile",
        service_id="future-service",
        path_name="future-path",
        status=HealthStatus.CRITICAL,
    )
    transport_health = SourceTransportHealth(
        service_id="future-service",
        path_name="future-path",
        source_type="futureSource",
        status=HealthStatus.DEGRADED,
        reason="no traffic",
    )

    result = evaluator.evaluate(
        media_health=media_health,
        transport_health=transport_health,
    )

    assert result.status is HealthStatus.CRITICAL
    assert result.reason == "media critical"


def test_transport_reason_does_not_override_degraded_media_when_transport_is_unknown() -> None:
    evaluator = SignalHealthEvaluator()

    media_health = MediaHealth(
        profile_id="future-profile",
        service_id="future-service",
        path_name="future-path",
        status=HealthStatus.DEGRADED,
    )
    transport_health = SourceTransportHealth(
        service_id="future-service",
        path_name="future-path",
        source_type="futureSource",
        status=HealthStatus.UNKNOWN,
        reason="telemetry unavailable",
    )

    result = evaluator.evaluate(
        media_health=media_health,
        transport_health=transport_health,
    )

    assert result.status is HealthStatus.DEGRADED
    assert result.reason == "media degraded"


def test_signal_falls_back_to_generic_transport_reason_when_detailed_reason_is_absent() -> None:
    evaluator = SignalHealthEvaluator()

    media_health = MediaHealth(
        profile_id="future-profile",
        service_id="future-service",
        path_name="future-path",
        status=HealthStatus.HEALTHY,
    )
    transport_health = SourceTransportHealth(
        service_id="future-service",
        path_name="future-path",
        source_type="futureSource",
        status=HealthStatus.DEGRADED,
        reason=None,
    )

    result = evaluator.evaluate(
        media_health=media_health,
        transport_health=transport_health,
    )

    assert result.status is HealthStatus.DEGRADED
    assert result.reason == "transport degraded"
