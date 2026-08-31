from datetime import datetime, timedelta, timezone

import pytest

from app.domain.streaming.metrics import (
    MeasurementQuality,
    StreamingPathMeasurement,
)
from app.domain.streaming.models import (
    MediaPath,
    MediaPathStatus,
    MediaSource,
)
from app.noc.domain.critical_path_policy import (
    CriticalPathPolicy,
)
from app.noc.domain.node_alarm import (
    AlarmSeverity,
    AlarmState,
)
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.services.critical_path_traffic_evaluator import (
    CriticalPathTrafficEvaluation,
    CriticalPathTrafficState,
)
from app.noc.services.critical_path_traffic_stabilizer import (
    CriticalPathTrafficStabilization,
)
from app.noc.services.critical_path_traffic_stalled_alarm_factory import (
    CRITICAL_PATH_TRAFFIC_STALLED,
    CriticalPathTrafficStalledAlarmFactory,
)


NOW = datetime(
    2026,
    8,
    31,
    8,
    0,
    tzinfo=timezone.utc,
)


def make_media_path() -> MediaPath:
    return MediaPath(
        name="ejtv",
        configuration_name="ejtv",
        status=MediaPathStatus.ACTIVE,
        ready=True,
        available=True,
        online=True,
        source=MediaSource(
            source_type="mpegtsSource"
        ),
    )


def make_measurement(
    bitrate: float = 0.0,
) -> StreamingPathMeasurement:
    return StreamingPathMeasurement(
        name="ejtv",
        status=MediaPathStatus.ACTIVE,
        previous_status=MediaPathStatus.ACTIVE,
        reader_count=2,
        reader_delta=0,
        inbound_delta_bytes=0,
        outbound_delta_bytes=0,
        inbound_bitrate_bps=bitrate,
        outbound_bitrate_bps=0.0,
        state_changed=False,
        quality=MeasurementQuality.AVAILABLE,
    )


def make_stabilization(
    *,
    confirmed: bool = True,
    state: CriticalPathTrafficState = (
        CriticalPathTrafficState.STALLED
    ),
) -> CriticalPathTrafficStabilization:
    policy = CriticalPathPolicy(path="ejtv")

    if state is CriticalPathTrafficState.STALLED:
        evaluation = CriticalPathTrafficEvaluation(
            policy=policy,
            state=state,
            media_path=make_media_path(),
            measurement=make_measurement(),
        )

        return CriticalPathTrafficStabilization(
            evaluation=evaluation,
            observed_at=NOW,
            stalled_since=NOW - timedelta(seconds=15),
            confirmed_stalled=confirmed,
        )

    if state is CriticalPathTrafficState.HEALTHY:
        evaluation = CriticalPathTrafficEvaluation(
            policy=policy,
            state=state,
            media_path=make_media_path(),
            measurement=make_measurement(
                bitrate=4_500_000.0
            ),
        )
    elif state is CriticalPathTrafficState.UNKNOWN:
        evaluation = CriticalPathTrafficEvaluation(
            policy=policy,
            state=state,
            media_path=make_media_path(),
            measurement=None,
        )
    else:
        evaluation = CriticalPathTrafficEvaluation(
            policy=policy,
            state=state,
            media_path=None,
            measurement=None,
        )

    return CriticalPathTrafficStabilization(
        evaluation=evaluation,
        observed_at=NOW,
        stalled_since=None,
        confirmed_stalled=False,
    )


def make_instance_id() -> NodeInstanceId:
    return NodeInstanceId("instance-001")


def test_create_confirmed_stalled_alarm() -> None:
    factory = CriticalPathTrafficStalledAlarmFactory()

    alarm = factory.create(
        stabilization=make_stabilization(),
        source=make_instance_id(),
        timestamp=NOW,
    )

    assert alarm.alarm_type == CRITICAL_PATH_TRAFFIC_STALLED
    assert alarm.severity is AlarmSeverity.CRITICAL
    assert alarm.state is AlarmState.ACTIVE
    assert alarm.source == make_instance_id()
    assert alarm.timestamp == NOW

    assert alarm.attributes["path"] == "ejtv"
    assert alarm.attributes["status"] == "ACTIVE"
    assert alarm.attributes["source_present"] == "true"
    assert alarm.attributes["source_type"] == "mpegtsSource"
    assert alarm.attributes["ready"] == "true"
    assert alarm.attributes["available"] == "true"
    assert alarm.attributes["online"] == "true"
    assert alarm.attributes["reader_count"] == "2"
    assert alarm.attributes["inbound_bitrate_bps"] == "0.0"
    assert (
        alarm.attributes["measurement_quality"]
        == "AVAILABLE"
    )


def test_alarm_ids_are_unique() -> None:
    factory = CriticalPathTrafficStalledAlarmFactory()

    first = factory.create(
        stabilization=make_stabilization(),
        source=make_instance_id(),
        timestamp=NOW,
    )

    second = factory.create(
        stabilization=make_stabilization(),
        source=make_instance_id(),
        timestamp=NOW,
    )

    assert first.alarm_id != second.alarm_id


def test_unconfirmed_stalled_is_rejected() -> None:
    factory = CriticalPathTrafficStalledAlarmFactory()

    with pytest.raises(ValueError):
        factory.create(
            stabilization=make_stabilization(
                confirmed=False
            ),
            source=make_instance_id(),
            timestamp=NOW,
        )


@pytest.mark.parametrize(
    "state",
    (
        CriticalPathTrafficState.HEALTHY,
        CriticalPathTrafficState.UNKNOWN,
        CriticalPathTrafficState.INACTIVE,
    ),
)
def test_non_stalled_state_is_rejected(
    state: CriticalPathTrafficState,
) -> None:
    factory = CriticalPathTrafficStalledAlarmFactory()

    with pytest.raises(ValueError):
        factory.create(
            stabilization=make_stabilization(
                state=state
            ),
            source=make_instance_id(),
            timestamp=NOW,
        )


def test_invalid_stabilization_type_is_rejected() -> None:
    factory = CriticalPathTrafficStalledAlarmFactory()

    with pytest.raises(TypeError):
        factory.create(
            stabilization=object(),  # type: ignore[arg-type]
            source=make_instance_id(),
            timestamp=NOW,
        )


def test_invalid_source_type_is_rejected() -> None:
    factory = CriticalPathTrafficStalledAlarmFactory()

    with pytest.raises(TypeError):
        factory.create(
            stabilization=make_stabilization(),
            source=object(),  # type: ignore[arg-type]
            timestamp=NOW,
        )


def test_naive_timestamp_is_rejected() -> None:
    factory = CriticalPathTrafficStalledAlarmFactory()

    with pytest.raises(ValueError):
        factory.create(
            stabilization=make_stabilization(),
            source=make_instance_id(),
            timestamp=datetime(2026, 8, 31, 8, 0),
        )


def test_non_utc_timestamp_is_rejected() -> None:
    factory = CriticalPathTrafficStalledAlarmFactory()

    non_utc = datetime(
        2026,
        8,
        31,
        2,
        0,
        tzinfo=timezone(timedelta(hours=-6)),
    )

    with pytest.raises(ValueError):
        factory.create(
            stabilization=make_stabilization(),
            source=make_instance_id(),
            timestamp=non_utc,
        )
