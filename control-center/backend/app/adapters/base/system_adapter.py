"""Contrato para consultar información del sistema administrado."""
from app.domain.system import ServiceMonitoringSnapshot

from abc import ABC, abstractmethod

from app.domain.system import (
    CPUInfo,
    DiskInfo,
    MemoryInfo,
    UptimeInfo,
)


class SystemAdapter(ABC):
    """Contrato de acceso a información del sistema."""

    @abstractmethod
    def hostname(self) -> str:
        """Retorna el nombre del equipo."""

    @abstractmethod
    def operating_system(self) -> str:
        """Retorna el nombre y versión del sistema operativo."""

    @abstractmethod
    def kernel(self) -> str:
        """Retorna la versión del kernel."""

    @abstractmethod
    def cpu_info(self) -> CPUInfo:
        """Retorna el estado actual del procesador."""

    @abstractmethod
    def memory_info(self) -> MemoryInfo:
        """Retorna el estado actual de la memoria principal."""

    @abstractmethod
    def disk_info(self) -> DiskInfo:
        """Retorna el estado del almacenamiento principal."""

    @abstractmethod
    def uptime_info(self) -> UptimeInfo:
        """Retorna el tiempo de funcionamiento del sistema."""

    @abstractmethod
    def service_monitoring(self) -> ServiceMonitoringSnapshot:
        """Retorna el estado de los servicios monitoreados."""