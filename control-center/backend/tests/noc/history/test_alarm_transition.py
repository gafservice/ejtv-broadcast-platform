from datetime import datetime, timedelta, timezone

import pytest

from app.noc.domain.node_alarm import AlarmState
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.history.alarm_transition import (
    AlarmTransition,
    AlarmTransitionType,
)


UTC_NOW = datetime(
    2026,
    9,
    1,
    12,
    0,
    0,
    tzinfo=timezone.utc,
)


def make_transition(**overrides) -> AlarmTransition:
    values = {
        "transition_id": "transition-001",
        "alarm_id": "alarm-001",
        "transition_type": AlarmTransitionType.OPENED,
        "timestamp": UTC_NOW,
        "source": NodeInstanceId("instance-001"),
        "state": AlarmState.ACTIVE,
    }
    values.update(overrides)
    return AlarmTransition(**values)


def test_alarm_transition_is_created() -> None:
    transition = make_transition()

    assert transition.transition_id == "transition-001"
    assert transition.alarm_id == "alarm-001"
    assert transition.transition_type is AlarmTransitionType.OPENED
    assert transition.timestamp == UTC_NOW
    assert transition.source == NodeInstanceId("instance-001")
    assert transition.state is AlarmState.ACTIVE
    assert transition.actor is None
    assert transition.metadata is None


def test_required_strings_are_normalized() -> None:
    transition = make_transition(
        transition_id="  transition-001  ",
        alarm_id="  alarm-001  ",
    )

    assert transition.transition_id == "transition-001"
    assert transition.alarm_id == "alarm-001"


@pytest.mark.parametrize(
    "field_name",
    [
        "transition_id",
        "alarm_id",
    ],
)
def test_required_string_rejects_empty(
    field_name: str,
) -> None:
    with pytest.raises(ValueError):
        make_transition(**{field_name: "   "})


@pytest.mark.parametrize(
    "field_name",
    [
        "transition_id",
        "alarm_id",
    ],
)
def test_required_string_rejects_non_string(
    field_name: str,
) -> None:
    with pytest.raises(TypeError):
        make_transition(**{field_name: 123})


def test_transition_type_must_be_enum() -> None:
    with pytest.raises(TypeError):
        make_transition(transition_type="OPENED")


def test_source_must_be_node_instance_id() -> None:
    with pytest.raises(TypeError):
        make_transition(source="instance-001")


def test_state_must_be_alarm_state() -> None:
    with pytest.raises(TypeError):
        make_transition(state="ACTIVE")


def test_timestamp_must_be_datetime() -> None:
    with pytest.raises(TypeError):
        make_transition(timestamp="2026-09-01T12:00:00Z")


def test_timestamp_must_be_timezone_aware() -> None:
    with pytest.raises(ValueError):
        make_transition(
            timestamp=datetime(2026, 9, 1, 12, 0, 0)
        )


def test_timestamp_must_be_utc() -> None:
    non_utc = timezone(timedelta(hours=-6))

    with pytest.raises(ValueError):
        make_transition(
            timestamp=datetime(
                2026,
                9,
                1,
                6,
                0,
                0,
                tzinfo=non_utc,
            )
        )


def test_actor_is_normalized() -> None:
    transition = make_transition(
        actor="  operator-01  "
    )

    assert transition.actor == "operator-01"


def test_blank_actor_becomes_none() -> None:
    transition = make_transition(actor="   ")

    assert transition.actor is None


def test_actor_rejects_non_string() -> None:
    with pytest.raises(TypeError):
        make_transition(actor=123)


def test_metadata_is_normalized_and_immutable() -> None:
    transition = make_transition(
        metadata={
            " path ": " ejtv ",
            "reason": " traffic stalled ",
        }
    )

    assert transition.metadata == {
        "path": "ejtv",
        "reason": "traffic stalled",
    }

    with pytest.raises(TypeError):
        transition.metadata["path"] = "impact"


def test_metadata_rejects_non_string_key() -> None:
    with pytest.raises(TypeError):
        make_transition(
            metadata={1: "value"}
        )


def test_metadata_rejects_non_string_value() -> None:
    with pytest.raises(TypeError):
        make_transition(
            metadata={"path": 123}
        )


def test_metadata_rejects_empty_key() -> None:
    with pytest.raises(ValueError):
        make_transition(
            metadata={"   ": "value"}
        )


@pytest.mark.parametrize(
    "transition_type",
    tuple(AlarmTransitionType),
)
def test_all_transition_types_are_supported(
    transition_type: AlarmTransitionType,
) -> None:
    transition = make_transition(
        transition_type=transition_type
    )

    assert transition.transition_type is transition_type


def test_deterministic_transition_id_is_stable() -> None:
    from app.noc.history.alarm_transition import (
        make_alarm_transition_id,
    )

    first = make_alarm_transition_id(
        alarm_id="alarm-001",
        transition_type=AlarmTransitionType.OPENED,
        timestamp=UTC_NOW,
        source=NodeInstanceId("instance-001"),
        state=AlarmState.ACTIVE,
    )

    second = make_alarm_transition_id(
        alarm_id="alarm-001",
        transition_type=AlarmTransitionType.OPENED,
        timestamp=UTC_NOW,
        source=NodeInstanceId("instance-001"),
        state=AlarmState.ACTIVE,
    )

    assert first == second
    assert first.startswith(
        "alarm-transition:"
    )
    assert len(first) == len(
        "alarm-transition:"
    ) + 64


@pytest.mark.parametrize(
    (
        "field_name",
        "different_value",
    ),
    [
        (
            "alarm_id",
            "alarm-002",
        ),
        (
            "transition_type",
            AlarmTransitionType.RESOLVED,
        ),
        (
            "timestamp",
            datetime(
                2026,
                9,
                1,
                12,
                0,
                1,
                tzinfo=timezone.utc,
            ),
        ),
        (
            "source",
            NodeInstanceId("instance-002"),
        ),
        (
            "state",
            AlarmState.RESOLVED,
        ),
    ],
)
def test_deterministic_transition_id_changes_with_identity(
    field_name,
    different_value,
) -> None:
    from app.noc.history.alarm_transition import (
        make_alarm_transition_id,
    )

    values = {
        "alarm_id": "alarm-001",
        "transition_type": AlarmTransitionType.OPENED,
        "timestamp": UTC_NOW,
        "source": NodeInstanceId("instance-001"),
        "state": AlarmState.ACTIVE,
    }

    original = make_alarm_transition_id(
        **values
    )

    values[field_name] = different_value

    changed = make_alarm_transition_id(
        **values
    )

    assert changed != original


def test_deterministic_transition_id_normalizes_alarm_id() -> None:
    from app.noc.history.alarm_transition import (
        make_alarm_transition_id,
    )

    clean = make_alarm_transition_id(
        alarm_id="alarm-001",
        transition_type=AlarmTransitionType.OPENED,
        timestamp=UTC_NOW,
        source=NodeInstanceId("instance-001"),
        state=AlarmState.ACTIVE,
    )

    padded = make_alarm_transition_id(
        alarm_id="  alarm-001  ",
        transition_type=AlarmTransitionType.OPENED,
        timestamp=UTC_NOW,
        source=NodeInstanceId("instance-001"),
        state=AlarmState.ACTIVE,
    )

    assert padded == clean


def test_invalidated_transition_type_is_supported() -> None:
    assert (
        AlarmTransitionType.INVALIDATED.value
        == "INVALIDATED"
    )
