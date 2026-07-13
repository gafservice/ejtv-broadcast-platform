"""Pruebas del contrato y del adaptador Linux."""

import inspect
from unittest.mock import patch

from app.adapters.base.system_adapter import SystemAdapter
from app.adapters.linux.linux_system_adapter import LinuxSystemAdapter


def test_system_adapter_is_abstract() -> None:
    assert inspect.isabstract(SystemAdapter)


def test_linux_adapter_implements_system_contract() -> None:
    assert issubclass(LinuxSystemAdapter, SystemAdapter)


def test_linux_adapter_is_concrete() -> None:
    assert not inspect.isabstract(LinuxSystemAdapter)


def test_hostname() -> None:
    adapter = LinuxSystemAdapter()

    with patch(
        "app.adapters.linux.linux_system_adapter.socket.gethostname",
        return_value="ejtv-01",
    ):
        assert adapter.hostname() == "ejtv-01"


def test_operating_system_uses_pretty_name() -> None:
    adapter = LinuxSystemAdapter()

    with patch(
        "app.adapters.linux.linux_system_adapter."
        "platform.freedesktop_os_release",
        return_value={
            "NAME": "Ubuntu",
            "VERSION": "24.04.4 LTS",
            "PRETTY_NAME": "Ubuntu 24.04.4 LTS",
        },
    ):
        assert adapter.operating_system() == "Ubuntu 24.04.4 LTS"


def test_operating_system_fallback() -> None:
    adapter = LinuxSystemAdapter()

    with (
        patch(
            "app.adapters.linux.linux_system_adapter."
            "platform.freedesktop_os_release",
            side_effect=OSError,
        ),
        patch(
            "app.adapters.linux.linux_system_adapter.platform.platform",
            return_value="Linux-6.8.0-x86_64",
        ),
    ):
        assert adapter.operating_system() == "Linux-6.8.0-x86_64"


def test_kernel() -> None:
    adapter = LinuxSystemAdapter()

    with patch(
        "app.adapters.linux.linux_system_adapter.platform.release",
        return_value="6.8.0-71-generic",
    ):
        assert adapter.kernel() == "6.8.0-71-generic"
