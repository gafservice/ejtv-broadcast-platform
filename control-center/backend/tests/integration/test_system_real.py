"""Prueba de integración con el sistema Linux real."""

import sys

import pytest

from app.api.dependencies import get_system_service
from app.domain.system import SystemInfo

pytestmark = pytest.mark.skipif(
    sys.platform != "linux",
    reason="La implementación actual requiere un sistema Linux.",
)


def test_real_linux_system_information() -> None:
    get_system_service.cache_clear()

    service = get_system_service()
    result = service.get_system_info()

    assert isinstance(result, SystemInfo)
    assert result.hostname
    assert result.operating_system
    assert result.kernel
