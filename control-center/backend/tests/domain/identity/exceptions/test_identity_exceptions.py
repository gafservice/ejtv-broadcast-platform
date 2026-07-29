import pytest

from app.domain.identity.exceptions import (
    IdentityError,
    InvalidCredentials,
    PermissionDenied,
    UserDisabled,
    UserLocked,
    UserNotFound,
)


@pytest.mark.parametrize(
    "exception_type",
    [
        InvalidCredentials,
        PermissionDenied,
        UserDisabled,
        UserLocked,
        UserNotFound,
    ],
)
def test_identity_exceptions_inherit_from_identity_error(
    exception_type: type[IdentityError],
) -> None:
    assert issubclass(exception_type, IdentityError)


@pytest.mark.parametrize(
    "exception_type",
    [
        IdentityError,
        InvalidCredentials,
        PermissionDenied,
        UserDisabled,
        UserLocked,
        UserNotFound,
    ],
)
def test_identity_exceptions_preserve_message(
    exception_type: type[IdentityError],
) -> None:
    message = "identity domain error"

    error = exception_type(message)

    assert str(error) == message


def test_identity_error_can_be_raised_and_caught() -> None:
    with pytest.raises(IdentityError, match="identity failure"):
        raise IdentityError("identity failure")


@pytest.mark.parametrize(
    "exception_type",
    [
        InvalidCredentials,
        PermissionDenied,
        UserDisabled,
        UserLocked,
        UserNotFound,
    ],
)
def test_specific_identity_errors_can_be_caught_as_base_error(
    exception_type: type[IdentityError],
) -> None:
    with pytest.raises(IdentityError):
        raise exception_type("identity failure")
