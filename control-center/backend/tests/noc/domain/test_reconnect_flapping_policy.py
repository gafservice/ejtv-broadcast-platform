from datetime import timedelta

import pytest

from app.noc.domain.reconnect_flapping_policy import (
    ReconnectFlappingPolicy,
)


def test_default_policy_values() -> None:
    policy = ReconnectFlappingPolicy()

    assert (
        policy.reconnect_timeout
        == timedelta(seconds=10)
    )
    assert (
        policy.window
        == timedelta(seconds=60)
    )
    assert policy.threshold == 3


def test_custom_policy_values() -> None:
    policy = ReconnectFlappingPolicy(
        reconnect_timeout=timedelta(seconds=5),
        window=timedelta(seconds=120),
        threshold=4,
    )

    assert (
        policy.reconnect_timeout
        == timedelta(seconds=5)
    )
    assert (
        policy.window
        == timedelta(seconds=120)
    )
    assert policy.threshold == 4


def test_reconnect_timeout_may_equal_window() -> None:
    policy = ReconnectFlappingPolicy(
        reconnect_timeout=timedelta(seconds=30),
        window=timedelta(seconds=30),
        threshold=2,
    )

    assert (
        policy.reconnect_timeout
        == policy.window
    )


@pytest.mark.parametrize(
    (
        "field_name",
        "value",
        "expected_exception",
        "expected_message",
    ),
    (
        (
            "reconnect_timeout",
            10,
            TypeError,
            "reconnect_timeout must be a timedelta",
        ),
        (
            "reconnect_timeout",
            timedelta(0),
            ValueError,
            "reconnect_timeout must be greater than zero",
        ),
        (
            "reconnect_timeout",
            timedelta(seconds=-1),
            ValueError,
            "reconnect_timeout must be greater than zero",
        ),
        (
            "window",
            60,
            TypeError,
            "window must be a timedelta",
        ),
        (
            "window",
            timedelta(0),
            ValueError,
            "window must be greater than zero",
        ),
        (
            "window",
            timedelta(seconds=-1),
            ValueError,
            "window must be greater than zero",
        ),
        (
            "threshold",
            3.0,
            TypeError,
            "threshold must be an int",
        ),
        (
            "threshold",
            True,
            TypeError,
            "threshold must be an int",
        ),
        (
            "threshold",
            1,
            ValueError,
            "threshold must be at least 2",
        ),
    ),
)
def test_invalid_policy_values(
    field_name,
    value,
    expected_exception,
    expected_message,
) -> None:
    arguments = {
        "reconnect_timeout": timedelta(seconds=10),
        "window": timedelta(seconds=60),
        "threshold": 3,
    }

    arguments[field_name] = value

    with pytest.raises(
        expected_exception,
        match=expected_message,
    ):
        ReconnectFlappingPolicy(
            **arguments,
        )


def test_reconnect_timeout_cannot_exceed_window() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "reconnect_timeout must not exceed window"
        ),
    ):
        ReconnectFlappingPolicy(
            reconnect_timeout=timedelta(seconds=61),
            window=timedelta(seconds=60),
            threshold=3,
        )
