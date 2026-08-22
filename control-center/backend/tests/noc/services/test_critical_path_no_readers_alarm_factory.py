from datetime import UTC, datetime, timedelta

import pytest

from app.domain.sessions import (
    ActiveSession,
    SessionProtocol,
    SessionRole,
)
from app.noc.domain.critical_path_policy import (
    CriticalPathPolicy,
)
from app.noc.domain.node_alarm import (
    AlarmSeverity,
    AlarmState,
)
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.services.critical_path_no_readers_alarm_factory import (
    CRITICAL_PATH_NO_READERS,
    CriticalPathNoReadersAlarmFactory,
)
from app.noc.services.critical_path_reader_evaluator import (
    CriticalPathReaderEvaluation,
    CriticalPathReaderState,
)
from app.noc.services.critical_path_reader_stabilizer import (
    CriticalPathReaderStabilization,
)


TIMESTAMP = datetime(
    2026,
    8,
    23,
    3,
    30,
    tzinfo=UTC,
)


def build_publisher() -> ActiveSession:
    return ActiveSession(
        session_id="publisher-1",
        protocol=SessionProtocol.SRT,
        role=SessionRole.PUBLISHER,
        state="publish",
        remote_ip="201.192.154.132",
        remote_port=50000,
        path="ejtv",
        connected_since=TIMESTAMP,
    )


def build_stabilization(
    *,
    confirmed_no_readers: bool = True,
) -> CriticalPathReaderStabilization:
    policy = CriticalPathPolicy(
        path="ejtv",
        no_readers_grace_period=timedelta(
            seconds=15
        ),
    )

    evaluation = CriticalPathReaderEvaluation(
        policy=policy,
        state=CriticalPathReaderState.NO_READERS,
        publishers=(
            build_publisher(),
        ),
        readers=(),
    )

    return CriticalPathReaderStabilization(
        evaluation=evaluation,
        observed_at=TIMESTAMP,
        no_readers_since=(
            TIMESTAMP - timedelta(seconds=15)
        ),
        confirmed_no_readers=confirmed_no_readers,
    )


def test_create_critical_path_no_readers_alarm() -> None:
    factory = CriticalPathNoReadersAlarmFactory()

    alarm = factory.create(
        stabilization=build_stabilization(),
        source=NodeInstanceId(
            "streaming-primary"
        ),
        timestamp=TIMESTAMP,
    )

    assert alarm.alarm_type == CRITICAL_PATH_NO_READERS
    assert alarm.severity is AlarmSeverity.MAJOR
    assert alarm.state is AlarmState.ACTIVE
    assert alarm.timestamp == TIMESTAMP


def test_alarm_contains_path_identity() -> None:
    factory = CriticalPathNoReadersAlarmFactory()

    alarm = factory.create(
        stabilization=build_stabilization(),
        source=NodeInstanceId(
            "streaming-primary"
        ),
        timestamp=TIMESTAMP,
    )

    assert alarm.attributes["path"] == "ejtv"
    assert alarm.attributes["publisher_count"] == "1"
    assert alarm.attributes["reader_count"] == "0"


def test_alarm_title_contains_path() -> None:
    factory = CriticalPathNoReadersAlarmFactory()

    alarm = factory.create(
        stabilization=build_stabilization(),
        source=NodeInstanceId(
            "streaming-primary"
        ),
        timestamp=TIMESTAMP,
    )

    assert "ejtv" in alarm.title


def test_alarm_id_is_unique() -> None:
    factory = CriticalPathNoReadersAlarmFactory()

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


def test_unconfirmed_state_cannot_create_alarm() -> None:
    factory = CriticalPathNoReadersAlarmFactory()

    with pytest.raises(
        ValueError,
        match=(
            "stabilization must represent confirmed "
            "no-readers state"
        ),
    ):
        factory.create(
            stabilization=build_stabilization(
                confirmed_no_readers=False,
            ),
            source=NodeInstanceId(
                "streaming-primary"
            ),
            timestamp=TIMESTAMP,
        )


def test_invalid_stabilization_is_rejected() -> None:
    factory = CriticalPathNoReadersAlarmFactory()

    with pytest.raises(
        TypeError,
        match=(
            "stabilization must be a "
            "CriticalPathReaderStabilization"
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
    factory = CriticalPathNoReadersAlarmFactory()

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
    factory = CriticalPathNoReadersAlarmFactory()

    with pytest.raises(
        ValueError,
        match="timestamp must be timezone-aware and UTC",
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
                3,
                30,
            ),
        )
