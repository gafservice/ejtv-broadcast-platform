from datetime import timedelta

import pytest

from app.noc.domain.critical_path_policy import (
    CriticalPathPolicy,
)


def test_policy_normalizes_path() -> None:
    policy = CriticalPathPolicy(
        path="  ejtv  "
    )

    assert policy.path == "ejtv"


def test_policy_defaults_to_enabled() -> None:
    policy = CriticalPathPolicy(
        path="ejtv"
    )

    assert policy.enabled is True


def test_default_no_readers_grace_period() -> None:
    policy = CriticalPathPolicy(
        path="ejtv"
    )

    assert (
        policy.no_readers_grace_period
        == timedelta(seconds=15)
    )


def test_custom_no_readers_grace_period() -> None:
    policy = CriticalPathPolicy(
        path="ejtv",
        no_readers_grace_period=timedelta(
            seconds=30
        ),
    )

    assert (
        policy.no_readers_grace_period
        == timedelta(seconds=30)
    )


def test_zero_grace_period_is_supported() -> None:
    policy = CriticalPathPolicy(
        path="ejtv",
        no_readers_grace_period=timedelta(0),
    )

    assert (
        policy.no_readers_grace_period
        == timedelta(0)
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
            "path",
            123,
            TypeError,
            "path must be a string",
        ),
        (
            "path",
            "   ",
            ValueError,
            "path must not be empty",
        ),
        (
            "enabled",
            "yes",
            TypeError,
            "enabled must be a bool",
        ),
        (
            "no_readers_grace_period",
            15,
            TypeError,
            (
                "no_readers_grace_period must be "
                "a timedelta"
            ),
        ),
        (
            "no_readers_grace_period",
            timedelta(seconds=-1),
            ValueError,
            (
                "no_readers_grace_period must not "
                "be negative"
            ),
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
        "path": "ejtv",
        "enabled": True,
        "no_readers_grace_period": timedelta(
            seconds=15
        ),
    }

    arguments[field_name] = value

    with pytest.raises(
        expected_exception,
        match=expected_message,
    ):
        CriticalPathPolicy(
            **arguments,
        )
