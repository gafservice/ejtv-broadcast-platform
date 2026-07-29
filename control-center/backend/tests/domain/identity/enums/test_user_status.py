import pytest

from app.domain.identity.enums import UserStatus


def test_user_status_defines_expected_values() -> None:
    assert UserStatus.ACTIVE == "active"
    assert UserStatus.DISABLED == "disabled"
    assert UserStatus.LOCKED == "locked"


def test_user_status_contains_exactly_three_members() -> None:
    assert list(UserStatus) == [
        UserStatus.ACTIVE,
        UserStatus.DISABLED,
        UserStatus.LOCKED,
    ]


def test_user_status_is_string_compatible() -> None:
    assert isinstance(UserStatus.ACTIVE, str)
    assert str(UserStatus.ACTIVE) == "active"


def test_user_status_can_be_created_from_valid_value() -> None:
    assert UserStatus("active") is UserStatus.ACTIVE
    assert UserStatus("disabled") is UserStatus.DISABLED
    assert UserStatus("locked") is UserStatus.LOCKED


def test_user_status_rejects_unknown_value() -> None:
    with pytest.raises(ValueError):
        UserStatus("unknown")
