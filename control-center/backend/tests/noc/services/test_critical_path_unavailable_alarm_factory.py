"""Tests for critical-path unavailable alarm factory."""

from datetime import UTC, datetime, timedelta

import pytest

from app.domain.streaming.models import (
    MediaPath,
    MediaPathStatus,
)
from app.noc.domain.critical_path_policy import CriticalPathPolicy
from app.noc.domain.node_alarm import AlarmSeverity, AlarmState
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.services.critical_path_availability_evaluator import (
    CriticalPathAvailabilityEvaluation,
    CriticalPathAvailabilityState,
)
from app.noc.services.critical_path_availability_stabilizer import (
    CriticalPathAvailabilityStabilization,
)
from app.noc.services.critical_path_unavailable_alarm_factory import (
    CRITICAL_PATH_UNAVAILABLE,
    CriticalPathUnavailableAlarmFactory,
)


TIMESTAMP = datetime(
    2026, 8, 30, 4, 30, tzinfo=UTC
)


def build_stabilization(
    *,
    media_path: MediaPath | None = None,
    confirmed: bool = True,
) -> CriticalPathAvailabilityStabilization:
    policy = CriticalPathPolicy(
        path="ejtv",
        unavailable_grace_period=timedelta(seconds=15),
    )

    evaluation = CriticalPathAvailabilityEvaluation(
        policy=policy,
        state=CriticalPathAvailabilityState.UNAVAILABLE,
        media_path=media_path,
    )

    return CriticalPathAvailabilityStabilization(
        evaluation=evaluation,
        observed_at=TIMESTAMP,
        unavailable_since=(
            TIMESTAMP - timedelta(seconds=15)
        ),
        confirmed_unavailable=confirmed,
    )


def test_create_unavailable_alarm_for_missing_path() -> None:
    alarm = CriticalPathUnavailableAlarmFactory().create(
        stabilization=build_stabilization(),
        source=NodeInstanceId("streaming-primary"),
        timestamp=TIMESTAMP,
    )

    assert alarm.alarm_type == CRITICAL_PATH_UNAVAILABLE
    assert alarm.severity is AlarmSeverity.CRITICAL
    assert alarm.state is AlarmState.ACTIVE
    assert alarm.attributes["path"] == "ejtv"
    assert alarm.attributes["path_present"] == "false"
    assert alarm.attributes["status"] == "MISSING"
    assert alarm.attributes["source_present"] == "false"


def test_create_unavailable_alarm_for_no_source_path() -> None:
    path = MediaPath(
        name="ejtv",
        configuration_name="ejtv",
        status=MediaPathStatus.NO_SOURCE,
        ready=False,
        available=False,
        online=False,
        source=None,
    )

    alarm = CriticalPathUnavailableAlarmFactory().create(
        stabilization=build_stabilization(
            media_path=path,
        ),
        source=NodeInstanceId("streaming-primary"),
        timestamp=TIMESTAMP,
    )

    assert alarm.attributes["path_present"] == "true"
    assert alarm.attributes["status"] == "NO_SOURCE"
    assert alarm.attributes["source_present"] == "false"
    assert alarm.attributes["source_type"] == "none"
    assert alarm.attributes["ready"] == "false"
    assert alarm.attributes["available"] == "false"
    assert alarm.attributes["online"] == "false"


def test_title_contains_path() -> None:
    alarm = CriticalPathUnavailableAlarmFactory().create(
        stabilization=build_stabilization(),
        source=NodeInstanceId("streaming-primary"),
        timestamp=TIMESTAMP,
    )

    assert "ejtv" in alarm.title


def test_alarm_id_is_unique() -> None:
    factory = CriticalPathUnavailableAlarmFactory()

    first = factory.create(
        stabilization=build_stabilization(),
        source=NodeInstanceId("streaming-primary"),
        timestamp=TIMESTAMP,
    )
    second = factory.create(
        stabilization=build_stabilization(),
        source=NodeInstanceId("streaming-primary"),
        timestamp=TIMESTAMP,
    )

    assert first.alarm_id.startswith("alm-")
    assert second.alarm_id.startswith("alm-")
    assert first.alarm_id != second.alarm_id


def test_unconfirmed_state_cannot_create_alarm() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "stabilization must represent confirmed "
            "unavailable state"
        ),
    ):
        CriticalPathUnavailableAlarmFactory().create(
            stabilization=build_stabilization(
                confirmed=False,
            ),
            source=NodeInstanceId("streaming-primary"),
            timestamp=TIMESTAMP,
        )


def test_invalid_stabilization_is_rejected() -> None:
    with pytest.raises(
        TypeError,
        match=(
            "stabilization must be a "
            "CriticalPathAvailabilityStabilization"
        ),
    ):
        CriticalPathUnavailableAlarmFactory().create(
            stabilization="invalid",  # type: ignore[arg-type]
            source=NodeInstanceId("streaming-primary"),
            timestamp=TIMESTAMP,
        )


def test_invalid_source_is_rejected() -> None:
    with pytest.raises(
        TypeError,
        match="source must be a NodeInstanceId",
    ):
        CriticalPathUnavailableAlarmFactory().create(
            stabilization=build_stabilization(),
            source="invalid",  # type: ignore[arg-type]
            timestamp=TIMESTAMP,
        )


def test_naive_timestamp_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="timestamp must be timezone-aware and UTC",
    ):
        CriticalPathUnavailableAlarmFactory().create(
            stabilization=build_stabilization(),
            source=NodeInstanceId("streaming-primary"),
            timestamp=datetime(2026, 8, 30, 4, 30),
        )
