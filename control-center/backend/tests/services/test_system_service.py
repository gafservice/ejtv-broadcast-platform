"""Pruebas del servicio de información del sistema."""

from app.adapters.base.system_adapter import SystemAdapter
from app.domain.system import SystemInfo
from app.services.system_service import SystemService


class FakeSystemAdapter(SystemAdapter):
    """Adaptador controlado utilizado exclusivamente en pruebas."""

    def hostname(self) -> str:
        return "ejtv-test"

    def operating_system(self) -> str:
        return "Test Linux 1.0"

    def kernel(self) -> str:
        return "1.0.0-test"


def test_system_service_returns_system_info() -> None:
    service = SystemService(FakeSystemAdapter())

    result = service.get_system_info()

    assert isinstance(result, SystemInfo)
    assert result.hostname == "ejtv-test"
    assert result.operating_system == "Test Linux 1.0"
    assert result.kernel == "1.0.0-test"


def test_system_service_uses_adapter_contract() -> None:
    adapter: SystemAdapter = FakeSystemAdapter()
    service = SystemService(adapter)

    assert service.get_system_info() == SystemInfo(
        hostname="ejtv-test",
        operating_system="Test Linux 1.0",
        kernel="1.0.0-test",
    )
