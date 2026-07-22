"""Objetos de dominio relacionados con el sistema administrado."""

from dataclasses import dataclass
from datetime import datetime


def _validate_percentage(field_name: str, value: float) -> float:
    """Valida y normaliza un porcentaje entre 0 y 100."""

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(
            f"El campo '{field_name}' debe contener un valor numérico."
        )

    normalized_value = float(value)

    if not 0.0 <= normalized_value <= 100.0:
        raise ValueError(
            f"El campo '{field_name}' debe estar entre 0 y 100."
        )

    return normalized_value


def _validate_non_negative_integer(
    field_name: str,
    value: int,
) -> int:
    """Valida que un valor sea un entero mayor o igual que cero."""

    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(
            f"El campo '{field_name}' debe contener un número entero."
        )

    if value < 0:
        raise ValueError(
            f"El campo '{field_name}' no puede ser negativo."
        )

    return value


def _validate_positive_integer(
    field_name: str,
    value: int,
) -> int:
    """Valida que un valor sea un entero mayor que cero."""

    normalized_value = _validate_non_negative_integer(
        field_name,
        value,
    )

    if normalized_value == 0:
        raise ValueError(
            f"El campo '{field_name}' debe ser mayor que cero."
        )

    return normalized_value


@dataclass(frozen=True, slots=True)
class SystemInfo:
    """Información básica e inmutable de un sistema administrado."""

    hostname: str
    operating_system: str
    kernel: str

    def __post_init__(self) -> None:
        """Valida que los atributos esenciales contengan información."""

        fields = {
            "hostname": self.hostname,
            "operating_system": self.operating_system,
            "kernel": self.kernel,
        }

        for field_name, value in fields.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"El campo '{field_name}' debe contener texto válido."
                )

            object.__setattr__(self, field_name, value.strip())


@dataclass(frozen=True, slots=True)
class CPUInfo:
    """Estado general del procesador del sistema."""

    usage_percent: float
    logical_cores: int
    physical_cores: int | None
    frequency_mhz: float | None
    per_core_usage_percent: tuple[float, ...] = ()

    def __post_init__(self) -> None:
        """Valida la información del procesador."""

        object.__setattr__(
            self,
            "usage_percent",
            _validate_percentage(
                "usage_percent",
                self.usage_percent,
            ),
        )

        object.__setattr__(
            self,
            "logical_cores",
            _validate_positive_integer(
                "logical_cores",
                self.logical_cores,
            ),
        )

        if self.physical_cores is not None:
            object.__setattr__(
                self,
                "physical_cores",
                _validate_positive_integer(
                    "physical_cores",
                    self.physical_cores,
                ),
            )

        if self.frequency_mhz is not None:
            if (
                isinstance(self.frequency_mhz, bool)
                or not isinstance(self.frequency_mhz, (int, float))
                or self.frequency_mhz < 0
            ):
                raise ValueError(
                    "El campo 'frequency_mhz' debe contener un valor "
                    "numérico mayor o igual que cero."
                )

            object.__setattr__(
                self,
                "frequency_mhz",
                float(self.frequency_mhz),
            )

        if not isinstance(self.per_core_usage_percent, tuple):
            raise ValueError(
                "El campo 'per_core_usage_percent' debe ser una tupla."
            )

        normalized_core_usage = tuple(
            _validate_percentage(
                "per_core_usage_percent",
                value,
            )
            for value in self.per_core_usage_percent
        )

        if (
            normalized_core_usage
            and len(normalized_core_usage) != self.logical_cores
        ):
            raise ValueError(
                "La cantidad de mediciones por CPU lógica debe coincidir "
                "con 'logical_cores'."
            )

        object.__setattr__(
            self,
            "per_core_usage_percent",
            normalized_core_usage,
        )

    @property
    def minimum_core_usage_percent(self) -> float | None:
        """Retorna la menor utilización entre las CPU lógicas."""

        if not self.per_core_usage_percent:
            return None

        return min(self.per_core_usage_percent)

    @property
    def maximum_core_usage_percent(self) -> float | None:
        """Retorna la mayor utilización entre las CPU lógicas."""

        if not self.per_core_usage_percent:
            return None

        return max(self.per_core_usage_percent)


@dataclass(frozen=True, slots=True)
class MemoryInfo:
    """Estado de utilización de la memoria principal."""

    total_bytes: int
    available_bytes: int
    used_bytes: int
    usage_percent: float

    free_bytes: int = 0
    cached_bytes: int = 0 
    buffers_bytes: int = 0

    def __post_init__(self) -> None:
        """Valida la información de memoria."""

        for field_name in (
            "total_bytes",
            "available_bytes",
            "used_bytes",
            "free_bytes",
            "cached_bytes",
            "buffers_bytes",
        ):
            value = getattr(self, field_name)

            object.__setattr__(
                self,
                field_name,
                _validate_non_negative_integer(
                    field_name,
                    value,
                ),
            )

        if self.total_bytes == 0:
            raise ValueError(
                "El campo 'total_bytes' debe ser mayor que cero."
            )

        if self.available_bytes > self.total_bytes:
            raise ValueError(
                "'available_bytes' no puede superar 'total_bytes'."
            )

        if self.used_bytes > self.total_bytes:
            raise ValueError(
                "'used_bytes' no puede superar 'total_bytes'."
            )

        object.__setattr__(
            self,
            "usage_percent",
            _validate_percentage(
                "usage_percent",
                self.usage_percent,
            ),
        )


@dataclass(frozen=True, slots=True)
class DiskInfo:
    """Estado de utilización del almacenamiento principal."""

    total_bytes: int
    used_bytes: int
    free_bytes: int
    usage_percent: float
    device: str = "unknown"
    mount_point: str = "/"
    filesystem_type: str = "unknown"

    def __post_init__(self) -> None:
        """Valida la información de almacenamiento."""

        for field_name in (
            "total_bytes",
            "used_bytes",
            "free_bytes",
        ):
            value = getattr(self, field_name)

            object.__setattr__(
                self,
                field_name,
                _validate_non_negative_integer(
                    field_name,
                    value,
                ),
            )

        if self.total_bytes == 0:
            raise ValueError(
                "El campo 'total_bytes' debe ser mayor que cero."
            )

        if self.used_bytes > self.total_bytes:
            raise ValueError(
                "'used_bytes' no puede superar 'total_bytes'."
            )

        if self.free_bytes > self.total_bytes:
            raise ValueError(
                "'free_bytes' no puede superar 'total_bytes'."
            )

        object.__setattr__(
            self,
            "usage_percent",
            _validate_percentage(
                "usage_percent",
                self.usage_percent,
            ),
        )

        for field_name in (
            "device",
            "mount_point",
            "filesystem_type",
        ):
            value = getattr(self, field_name)

            if not isinstance(value, str):
                raise TypeError(
                    f"El campo '{field_name}' debe ser una cadena."
                )

            normalized_value = value.strip()

            if not normalized_value:
                raise ValueError(
                    f"El campo '{field_name}' no puede estar vacío."
                )

            object.__setattr__(
                self,
                field_name,
                normalized_value,
            )

@dataclass(frozen=True, slots=True)
class UptimeInfo:
    """Tiempo de funcionamiento continuo del sistema."""

    uptime_seconds: int

    def __post_init__(self) -> None:
        """Valida el tiempo de funcionamiento."""

        object.__setattr__(
            self,
            "uptime_seconds",
            _validate_non_negative_integer(
                "uptime_seconds",
                self.uptime_seconds,
            ),
        )


@dataclass(frozen=True, slots=True)
class NetworkInfo:
    """Contadores acumulados de una interfaz de red."""

    interface: str
    bytes_sent: int
    bytes_received: int
    packets_sent: int
    packets_received: int
    errors_in: int
    errors_out: int
    dropped_in: int
    dropped_out: int

    def __post_init__(self) -> None:
        """Valida la identidad y los contadores de red."""

        if not isinstance(self.interface, str):
            raise TypeError(
                "El campo 'interface' debe ser una cadena."
            )

        normalized_interface = self.interface.strip()

        if not normalized_interface:
            raise ValueError(
                "El campo 'interface' no puede estar vacío."
            )

        object.__setattr__(
            self,
            "interface",
            normalized_interface,
        )

        for field_name in (
            "bytes_sent",
            "bytes_received",
            "packets_sent",
            "packets_received",
            "errors_in",
            "errors_out",
            "dropped_in",
            "dropped_out",
        ):
            value = getattr(self, field_name)

            object.__setattr__(
                self,
                field_name,
                _validate_non_negative_integer(
                    field_name,
                    value,
                ),
            )
@dataclass(frozen=True, slots=True)
class SystemResources:
    """Medición consolidada de los recursos del servidor."""

    cpu: CPUInfo
    memory: MemoryInfo
    disk: DiskInfo
    network: NetworkInfo
    uptime: UptimeInfo
    captured_at: datetime

    def __post_init__(self) -> None:
        """Valida los componentes y el instante de medición."""

        expected_types = {
            "cpu": CPUInfo,
            "memory": MemoryInfo,
            "disk": DiskInfo,
            "network": NetworkInfo,
            "uptime": UptimeInfo,
        }

        for field_name, expected_type in expected_types.items():
            value = getattr(self, field_name)

            if not isinstance(value, expected_type):
                raise ValueError(
                    f"El campo '{field_name}' debe ser una instancia de "
                    f"{expected_type.__name__}."
                )

        if not isinstance(self.captured_at, datetime):
            raise ValueError(
                "El campo 'captured_at' debe contener una fecha válida."
            )

        if self.captured_at.tzinfo is None:
            raise ValueError(
                "El campo 'captured_at' debe incluir zona horaria."
            )
