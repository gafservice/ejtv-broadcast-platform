"""Servicios de aplicación relacionados con el sistema."""

from app.adapters.base.system_adapter import SystemAdapter
from app.domain.system import SystemInfo


class SystemService:
    """Coordina la obtención de información del sistema administrado."""

    def __init__(self, adapter: SystemAdapter) -> None:
        """Recibe cualquier implementación válida de SystemAdapter."""

        self._adapter = adapter

    def get_system_info(self) -> SystemInfo:
        """Obtiene y consolida la información básica del sistema."""

        return SystemInfo(
            hostname=self._adapter.hostname(),
            operating_system=self._adapter.operating_system(),
            kernel=self._adapter.kernel(),
        )
