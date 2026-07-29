from dataclasses import FrozenInstanceError

import pytest

from app.domain.identity.value_objects import PermissionName


INVALID_FORMAT_MESSAGE = (
    "PermissionName must contain at least two lowercase "
    "segments separated by dots; each segment must start "
    "with a lowercase letter and contain only lowercase "
    "letters, numbers, and underscores"
)


def test_permission_name_accepts_valid_value() -> None:
    permission_name = PermissionName("stream.read")

    assert permission_name.value == "stream.read"


def test_permission_name_strips_surrounding_whitespace() -> None:
    permission_name = PermissionName("  dashboard.view  ")

    assert permission_name.value == "dashboard.view"


@pytest.mark.parametrize(
    "raw_value",
    [
        "stream.read",
        "stream.publish",
        "dashboard.view",
        "dashboard.edit",
        "user.create",
        "user.delete",
        "system.metrics.read",
        "system.config.update",
        "alarm.ack",
        "alarm.clear",
        "stream_1.read_2",
        "a.b",
        "a1.b2",
        "noc.dashboard_view",
    ],
)
def test_permission_name_accepts_valid_formats(raw_value: str) -> None:
    assert PermissionName(raw_value).value == raw_value


def test_permission_name_accepts_multiple_segments() -> None:
    permission_name = PermissionName(
        "system.streaming.metrics.read"
    )

    assert permission_name.value == "system.streaming.metrics.read"


def test_permission_name_accepts_minimum_structural_length() -> None:
    permission_name = PermissionName("a.b")

    assert len(permission_name.value) == 3


def test_permission_name_accepts_maximum_length() -> None:
    raw_value = "a." + ("b" * 126)

    assert len(raw_value) == PermissionName.MAX_LENGTH
    assert PermissionName(raw_value).value == raw_value


def test_permission_name_rejects_non_string_value() -> None:
    with pytest.raises(
        TypeError,
        match="PermissionName value must be a string",
    ):
        PermissionName(123)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "raw_value",
    [
        "",
        " ",
        "a",
        "ab",
        "  ab  ",
    ],
)
def test_permission_name_rejects_value_shorter_than_minimum(
    raw_value: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="PermissionName must contain at least 3 characters",
    ):
        PermissionName(raw_value)


def test_permission_name_rejects_value_longer_than_maximum() -> None:
    raw_value = "a." + ("b" * 127)

    assert len(raw_value) == PermissionName.MAX_LENGTH + 1

    with pytest.raises(
        ValueError,
        match="PermissionName must contain at most 128 characters",
    ):
        PermissionName(raw_value)


@pytest.mark.parametrize(
    "raw_value",
    [
        "read",
        "Read",
        "STREAM.READ",
        "Stream.read",
        "stream.Read",
        "stream.READ",
        "stream-read",
        "stream read",
        ".read",
        "stream.",
        "stream..read",
        "stream...read",
        "_stream.read",
        "1stream.read",
        "stream._read",
        "stream.1read",
        "stream.-read",
        "stream.@read",
        "stream/read",
        "stream:read",
        "stream+read",
        "stream\nread",
        "stream\tread",
        "stream.\x00read",
        "stréam.read",
        "stream.réad",
    ],
)
def test_permission_name_rejects_invalid_format(
    raw_value: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=INVALID_FORMAT_MESSAGE,
    ):
        PermissionName(raw_value)


def test_permission_name_equality_is_based_on_value() -> None:
    assert (
        PermissionName("stream.read")
        == PermissionName("stream.read")
    )


def test_permission_name_inequality_is_based_on_value() -> None:
    assert (
        PermissionName("stream.read")
        != PermissionName("stream.publish")
    )


def test_permission_name_case_is_not_normalized() -> None:
    with pytest.raises(ValueError):
        PermissionName("Stream.Read")


def test_permission_name_is_hashable() -> None:
    permission_name = PermissionName("stream.read")

    assert {permission_name} == {
        PermissionName("stream.read")
    }


def test_permission_name_can_be_used_as_dictionary_key() -> None:
    permission_name = PermissionName("dashboard.view")

    permissions = {
        permission_name: True,
    }

    assert permissions[
        PermissionName("dashboard.view")
    ] is True


def test_permission_name_is_immutable() -> None:
    permission_name = PermissionName("stream.read")

    with pytest.raises(FrozenInstanceError):
        permission_name.value = "stream.publish"  # type: ignore[misc]


def test_permission_name_string_representation_returns_value() -> None:
    permission_name = PermissionName("stream.read")

    assert str(permission_name) == "stream.read"
