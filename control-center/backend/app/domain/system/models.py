"""Objetos de dominio relacionados con el sistema administrado."""

from dataclasses import dataclass


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
