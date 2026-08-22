from datetime import UTC, datetime, timedelta

import pytest

from app.domain.sessions import (
    SessionProtocol,
    SessionRole,
)
from app.noc.domain.expected_session_policy import (
    ExpectedSessionPolicy,
)
from app.noc.domain.node_alarm import (
    AlarmSeverity,
    AlarmState,
)
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.services.expected_session_alarm_factory import (
    EXPECTED_SESSION_MISSING,
    ExpectedSessionAlarmFactory,
)
from app.noc.services.expected_session_evaluator import (
    ExpectedSessionEvaluation,
    ExpectedSessionState,
)
from app.noc.services.expected_session_stabilizer import (
    ExpectedSessionStabilization,
)


TIMESTAMP = datetime(
    2026,
    8,
    23,
    0,
    0,
    tzinfo=UTC,
)


def build_stabilization(
    *,
    confirmed_missing: bool = True,
) -> ExpectedSessionStabilization:
    policy = ExpectedSessionPolicy(
        policy_id="ejtv-srt-reader",
        protocol=SessionProtocol.SRT,
        role=SessionRole.READER,
        path="ejtv",
        missing_grace_period=timedelta(seconds=15),
    )

    evaluation = ExpectedSessionEvaluation(
        policy=policy,
        state=ExpectedSessionState.MISSING,
        matching_sessions=(),
    )

    return ExpectedSessionStabilization(
        evaluation=evaluation,
        observed_at=TIMESTAMP,
        missing_since=TIMESTAMP - timedelta(seconds=15),
        confirmed_missing=confirmed_missing,
    )


def test_create_expected_session_missing_alarm() -> None:
    factory = ExpectedSessionAlarmFactory()

    alarm = factory.create(
        stabilization=build_stabilization(),
        source=NodeInstanceId(
            "streaming-primary"
        ),
        timestamp=TIMESTAMP,
    )

    assert alarm.alarm_type == EXPECTED_SESSION_MISSING
    assert alarm.severity is AlarmSeverity.MAJOR
    assert alarm.state is AlarmState.ACTIVE
    assert alarm.timestamp == TIMESTAMP


def test_alarm_contains_policy_identity() -> None:
    factory = ExpectedSessionAlarmFactory()

    alarm = factory.create(
        stabilization=build_stabilization(),
        source=NodeInstanceId(
            "streaming-primary"
        ),
        timestamp=TIMESTAMP,
    )

    assert (
        alarm.attributes["policy_id"]
        == "ejtv-srt-reader"
    )

    assert alarm.attributes["protocol"] == "SRT"
    assert alarm.attributes["role"] == "READER"
    assert alarm.attributes["path"] == "ejtv"


def test_alarm_title_contains_operational_context() -> None:
    factory = ExpectedSessionAlarmFactory()

    alarm = factory.create(
        stabilization=build_stabilization(),
        source=NodeInstanceId(
            "streaming-primary"
        ),
        timestamp=TIMESTAMP,
    )

    assert "SRT" in alarm.title
    assert "reader" in alarm.title
    assert "ejtv" in alarm.title


def test_alarm_id_is_unique() -> None:
    factory = ExpectedSessionAlarmFactory()

    first = factory.create(
        stabilization=build_stabilization(),
        source=NodeInstanceId(
            "streaming-primary"
        ),
        timestamp=TIMESTAMP,
    )

    second = factory.create(
        stabilization=build_stabilization(),
        source=NodeInstanceId(
            "streaming-primary"
        ),
        timestamp=TIMESTAMP,
    )

    assert first.alarm_id.startswith("alm-")
    assert second.alarm_id.startswith("alm-")
    assert first.alarm_id != second.alarm_id


def test_unconfirmed_missing_cannot_create_alarm() -> None:
    factory = ExpectedSessionAlarmFactory()

    with pytest.raises(
        ValueError,
        match=(
            "stabilization must represent a "
            "confirmed missing session"
        ),
    ):
        factory.create(
            stabilization=build_stabilization(
                confirmed_missing=False,
            ),
            source=NodeInstanceId(
                "streaming-primary"
            ),
            timestamp=TIMESTAMP,
        )


def test_invalid_stabilization_is_rejected() -> None:
    factory = ExpectedSessionAlarmFactory()

    with pytest.raises(
        TypeError,
        match=(
            "stabilization must be an "
            "ExpectedSessionStabilization"
        ),
    ):
        factory.create(
            stabilization="invalid",  # type: ignore[arg-type]
            source=NodeInstanceId(
                "streaming-primary"
            ),
            timestamp=TIMESTAMP,
        )


def test_invalid_source_is_rejected() -> None:
    factory = ExpectedSessionAlarmFactory()

    with pytest.raises(
        TypeError,
        match="source must be a NodeInstanceId",
    ):
        factory.create(
            stabilization=build_stabilization(),
            source="invalid",  # type: ignore[arg-type]
            timestamp=TIMESTAMP,
        )


def test_naive_timestamp_is_rejected() -> None:
    factory = ExpectedSessionAlarmFactory()

    with pytest.raises(
        ValueError,
        match="timestamp must be timezone-aware",
    ):
        factory.create(
            stabilization=build_stabilization(),
            source=NodeInstanceId(
                "streaming-primary"
            ),
            timestamp=datetime(
                2026,
                8,
                23,
                0,
                0,
            ),
        )
