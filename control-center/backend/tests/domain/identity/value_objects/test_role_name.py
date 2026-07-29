from dataclasses import FrozenInstanceError

import pytest

from app.domain.identity.value_objects import RoleName


def test_role_name_accepts_valid_value() -> None:
    role_name = RoleName("admin")

    assert role_name.value == "admin"


def test_role_name_strips_surrounding_whitespace() -> None:
    role_name = RoleName("  noc_viewer  ")

    assert role_name.value == "noc_viewer"


@pytest.mark.parametrize(
    "raw_value",
    [
        "admin",
        "operator",
        "noc_viewer",
        "broadcast_admin",
        "support_level_1",
        "a12",
        "abc",
    ],
)
def test_role_name_accepts_valid_formats(raw_value: str) -> None:
    assert RoleName(raw_value).value == raw_value


def test_role_name_accepts_minimum_length() -> None:
    role_name = RoleName("abc")

    assert role_name.value == "abc"


def test_role_name_accepts_maximum_length() -> None:
    raw_value = "a" + ("b" * 63)

    assert len(raw_value) == RoleName.MAX_LENGTH
    assert RoleName(raw_value).value == raw_value


def test_role_name_rejects_non_string_value() -> None:
    with pytest.raises(TypeError, match="RoleName value must be a string"):
        RoleName(123)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "raw_value",
    [
        "",
        " ",
        "ab",
        "  ab  ",
    ],
)
def test_role_name_rejects_value_shorter_than_minimum(
    raw_value: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="RoleName must contain at least 3 characters",
    ):
        RoleName(raw_value)


def test_role_name_rejects_value_longer_than_maximum() -> None:
    raw_value = "a" * (RoleName.MAX_LENGTH + 1)

    with pytest.raises(
        ValueError,
        match="RoleName must contain at most 64 characters",
    ):
        RoleName(raw_value)


@pytest.mark.parametrize(
    "raw_value",
    [
        "Admin",
        "ADMIN",
        "1admin",
        "_admin",
        "-admin",
        "admin-",
        "admin-user",
        "admin.user",
        "admin user",
        "admin@user",
        "ádmin",
        "noc/viewer",
        "admin\nuser",
        "admin\tuser",
        "admin\x00user",
    ],
)
def test_role_name_rejects_invalid_format(raw_value: str) -> None:
    with pytest.raises(
        ValueError,
        match=(
            "RoleName must start with a lowercase letter and contain only "
            "lowercase letters, numbers, and underscores"
        ),
    ):
        RoleName(raw_value)


def test_role_name_equality_is_based_on_value() -> None:
    assert RoleName("admin") == RoleName("admin")


def test_role_name_case_is_not_normalized() -> None:
    with pytest.raises(ValueError):
        RoleName("Admin")


def test_role_name_is_hashable() -> None:
    role_name = RoleName("admin")

    assert {role_name} == {RoleName("admin")}


def test_role_name_is_immutable() -> None:
    role_name = RoleName("admin")

    with pytest.raises(FrozenInstanceError):
        role_name.value = "operator"  # type: ignore[misc]


def test_role_name_string_representation_returns_value() -> None:
    role_name = RoleName("admin")

    assert str(role_name) == "admin"
