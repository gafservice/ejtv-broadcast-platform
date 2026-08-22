from datetime import UTC, datetime

import pytest

from app.domain.sessions import (
    SessionProtocol,
    SessionRole,
)
from app.noc.domain.logical_session_identity import (
    LogicalSessionIdentity,
)
from app.noc.domain.node_alarm import (
    AlarmSeverity,
    AlarmState,
)
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.services.reconnect_flapping_alarm_factory import (
    RECONNECT_FLAPPING,
    ReconnectFlappingAlarmFactory,
)
from app.noc.services.reconnect_flapping_evaluator import (
    ReconnectFlappingEvaluation,
    ReconnectFlappingState,
)


TIMESTAMP = datetime(
    2026,
    8,
    23,
    2,
    0,
    tzinfo=UTC,
)


def build_evaluation(
    *,
    state: ReconnectFlappingState = (
        ReconnectFlappingState.FLAPPING
    ),
) -> ReconnectFlappingEvaluation:
    identity = LogicalSessionIdentity(
        protocol=SessionProtocol.SRT,
        role=SessionRole.READER,
        path="ejtv",
        remote_ip="201.192.154.132",
    )

    reconnects = (
        TIMESTAMP,
        TIMESTAMP,
        TIMESTAMP,
    )

    return ReconnectFlappingEvaluation(
        identity=identity,
        state=state,
        observed_at=TIMESTAMP,
        reconnect_count=3,
        reconnect_timestamps=reconnects,
        reconnect_detected=True,
    )


def test_create_reconnect_flapping_alarm() -> None:
    factory = ReconnectFlappingAlarmFactory()

    alarm = factory.create(
        evaluation=build_evaluation(),
        source=NodeInstanceId(
            "streaming-primary"
        ),
        timestamp=TIMESTAMP,
    )

    assert alarm.alarm_type == RECONNECT_FLAPPING
    assert alarm.severity is AlarmSeverity.MAJOR
    assert alarm.state is AlarmState.ACTIVE
    assert alarm.timestamp == TIMESTAMP


def test_alarm_contains_logical_identity() -> None:
    factory = ReconnectFlappingAlarmFactory()

    alarm = factory.create(
        evaluation=build_evaluation(),
        source=NodeInstanceId(
            "streaming-primary"
        ),
        timestamp=TIMESTAMP,
    )

    assert alarm.attributes["protocol"] == "SRT"
    assert alarm.attributes["role"] == "READER"
    assert alarm.attributes["path"] == "ejtv"
    assert (
        alarm.attributes["remote_ip"]
        == "201.192.154.132"
    )
    assert alarm.attributes["reconnect_count"] == "3"


def test_alarm_title_contains_operational_context() -> None:
    factory = ReconnectFlappingAlarmFactory()

    alarm = factory.create(
        evaluation=build_evaluation(),
        source=NodeInstanceId(
            "streaming-primary"
        ),
        timestamp=TIMESTAMP,
    )

    assert "SRT" in alarm.title
    assert "reader" in alarm.title
    assert "ejtv" in alarm.title


def test_alarm_id_is_unique() -> None:
    factory = ReconnectFlappingAlarmFactory()

    first = factory.create(
        evaluation=build_evaluation(),
        source=NodeInstanceId(
            "streaming-primary"
        ),
        timestamp=TIMESTAMP,
    )

    second = factory.create(
        evaluation=build_evaluation(),
        source=NodeInstanceId(
            "streaming-primary"
        ),
        timestamp=TIMESTAMP,
    )

    assert first.alarm_id.startswith("alm-")
    assert second.alarm_id.startswith("alm-")
    assert first.alarm_id != second.alarm_id


def test_stable_evaluation_cannot_create_alarm() -> None:
    factory = ReconnectFlappingAlarmFactory()

    with pytest.raises(
        ValueError,
        match="evaluation must represent FLAPPING",
    ):
        factory.create(
            evaluation=build_evaluation(
                state=ReconnectFlappingState.STABLE,
            ),
            source=NodeInstanceId(
                "streaming-primary"
            ),
            timestamp=TIMESTAMP,
        )


def test_invalid_evaluation_is_rejected() -> None:
    factory = ReconnectFlappingAlarmFactory()

    with pytest.raises(
        TypeError,
        match=(
            "evaluation must be a "
            "ReconnectFlappingEvaluation"
        ),
    ):
        factory.create(
            evaluation="invalid",  # type: ignore[arg-type]
            source=NodeInstanceId(
                "streaming-primary"
            ),
            timestamp=TIMESTAMP,
        )


def test_invalid_source_is_rejected() -> None:
    factory = ReconnectFlappingAlarmFactory()

    with pytest.raises(
        TypeError,
        match="source must be a NodeInstanceId",
    ):
        factory.create(
            evaluation=build_evaluation(),
            source="invalid",  # type: ignore[arg-type]
            timestamp=TIMESTAMP,
        )


def test_naive_timestamp_is_rejected() -> None:
    factory = ReconnectFlappingAlarmFactory()

    with pytest.raises(
        ValueError,
        match="timestamp must be timezone-aware and UTC",
    ):
        factory.create(
            evaluation=build_evaluation(),
            source=NodeInstanceId(
                "streaming-primary"
            ),
            timestamp=datetime(
                2026,
                8,
                23,
                2,
                0,
            ),
        )
