"""Servicios de aplicación relacionados con el sistema."""

from datetime import UTC, datetime

from app.adapters.base.system_adapter import SystemAdapter
from app.domain.system import (
    ServiceMonitoringSnapshot,
    SystemInfo,
    SystemResources,
)


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

    def get_system_resources(self) -> SystemResources:
        """Obtiene y consolida los recursos actuales del sistema."""

        return SystemResources(
            cpu=self._adapter.cpu_info(),
            memory=self._adapter.memory_info(),
            disk=self._adapter.disk_info(),
            uptime=self._adapter.uptime_info(),
            captured_at=datetime.now(UTC),
        )   
    def get_service_monitoring(
        self,
        ) -> ServiceMonitoringSnapshot:
        """Obtiene el estado actual de los servicios monitoreados."""

        return self._adapter.service_monitoring()