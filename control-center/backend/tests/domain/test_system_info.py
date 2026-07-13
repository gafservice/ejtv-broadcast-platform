"""Pruebas del objeto de dominio SystemInfo."""

from dataclasses import FrozenInstanceError

import pytest

from app.domain.system import SystemInfo


def test_system_info_creation() -> None:
    system_info = SystemInfo(
        hostname="ejtv-01",
        operating_system="Ubuntu 24.04.4 LTS",
        kernel="6.17.0-35-generic",
    )

    assert system_info.hostname == "ejtv-01"
    assert system_info.operating_system == "Ubuntu 24.04.4 LTS"
    assert system_info.kernel == "6.17.0-35-generic"


def test_system_info_strips_whitespace() -> None:
    system_info = SystemInfo(
        hostname="  ejtv-01  ",
        operating_system="  Ubuntu 24.04.4 LTS  ",
        kernel="  6.17.0-35-generic  ",
    )

    assert system_info.hostname == "ejtv-01"
    assert system_info.operating_system == "Ubuntu 24.04.4 LTS"
    assert system_info.kernel == "6.17.0-35-generic"


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [
        ("hostname", ""),
        ("operating_system", "   "),
        ("kernel", ""),
    ],
)
def test_system_info_rejects_empty_values(
    field_name: str,
    field_value: str,
) -> None:
    values = {
        "hostname": "ejtv-01",
        "operating_system": "Ubuntu 24.04.4 LTS",
        "kernel": "6.17.0-35-generic",
    }
    values[field_name] = field_value

    with pytest.raises(ValueError):
        SystemInfo(**values)


def test_system_info_is_immutable() -> None:
    system_info = SystemInfo(
        hostname="ejtv-01",
        operating_system="Ubuntu 24.04.4 LTS",
        kernel="6.17.0-35-generic",
    )

    with pytest.raises(FrozenInstanceError):
        system_info.hostname = "otro-servidor"  # type: ignore[misc]
