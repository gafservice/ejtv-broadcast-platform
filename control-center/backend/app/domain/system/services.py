"""Objetos de dominio para monitoreo de servicios."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ServiceStatus(str, Enum):
    """Estados posibles de un servicio monitoreado."""

    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ServiceInstance:
    """Información de una instancia de proceso asociada a un servicio."""

    pid: int
    cpu_percent: float
    memory_bytes: int
    uptime_seconds: int

    def __post_init__(self) -> None:
        """Valida los valores de la instancia."""

        if isinstance(self.pid, bool) or not isinstance(self.pid, int):
            raise ValueError("El campo 'pid' debe ser un entero.")

        if self.pid <= 0:
            raise ValueError("El campo 'pid' debe ser mayor que cero.")

        if (
            isinstance(self.cpu_percent, bool)
            or not isinstance(self.cpu_percent, (int, float))
        ):
            raise ValueError(
                "El campo 'cpu_percent' debe contener un valor numérico."
            )

        if not 0.0 <= float(self.cpu_percent) <= 100.0:
            raise ValueError(
                "El campo 'cpu_percent' debe estar entre 0 y 100."
            )

        if (
            isinstance(self.memory_bytes, bool)
            or not isinstance(self.memory_bytes, int)
        ):
            raise ValueError(
                "El campo 'memory_bytes' debe ser un entero."
            )

        if self.memory_bytes < 0:
            raise ValueError(
                "El campo 'memory_bytes' no puede ser negativo."
            )

        if (
            isinstance(self.uptime_seconds, bool)
            or not isinstance(self.uptime_seconds, int)
        ):
            raise ValueError(
                "El campo 'uptime_seconds' debe ser un entero."
            )

        if self.uptime_seconds < 0:
            raise ValueError(
                "El campo 'uptime_seconds' no puede ser negativo."
            )

        object.__setattr__(
            self,
            "cpu_percent",
            float(self.cpu_percent),
        )


@dataclass(frozen=True, slots=True)
class MonitoredService:
    """Estado consolidado de un servicio monitoreado."""

    name: str
    identifier: str
    monitor_type: str
    status: ServiceStatus
    instances: tuple[ServiceInstance, ...]

    def __post_init__(self) -> None:
        """Valida la definición del servicio."""

        text_fields = {
            "name": self.name,
            "identifier": self.identifier,
            "monitor_type": self.monitor_type,
        }

        for field_name, value in text_fields.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"El campo '{field_name}' debe contener texto válido."
                )

            object.__setattr__(
                self,
                field_name,
                value.strip(),
            )

        if not isinstance(self.status, ServiceStatus):
            raise ValueError(
                "El campo 'status' debe ser una instancia de ServiceStatus."
            )

        if not isinstance(self.instances, tuple):
            raise ValueError(
                "El campo 'instances' debe ser una tupla."
            )

        for instance in self.instances:
            if not isinstance(instance, ServiceInstance):
                raise ValueError(
                    "Todas las instancias deben ser ServiceInstance."
                )


@dataclass(frozen=True, slots=True)
class ServiceMonitoringSnapshot:
    """Medición completa del estado de los servicios configurados."""

    services: tuple[MonitoredService, ...]
    captured_at: datetime

    def __post_init__(self) -> None:
        """Valida la medición consolidada."""

        if not isinstance(self.services, tuple):
            raise ValueError(
                "El campo 'services' debe ser una tupla."
            )

        for service in self.services:
            if not isinstance(service, MonitoredService):
                raise ValueError(
                    "Todos los servicios deben ser MonitoredService."
                )

        if not isinstance(self.captured_at, datetime):
            raise ValueError(
                "El campo 'captured_at' debe contener una fecha válida."
            )

        if self.captured_at.tzinfo is None:
            raise ValueError(
                "El campo 'captured_at' debe incluir zona horaria."
            )