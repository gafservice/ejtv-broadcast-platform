"""Modelos de presentación para el panel NODE HEALTH."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class NodeHealthInterfaceRowData:
    """Salud efectiva de una interfaz preparada para presentación."""

    interface: str
    state: str
    reason: str

    def __post_init__(self) -> None:
        for field_name in (
            "interface",
            "state",
            "reason",
        ):
            value = getattr(
                self,
                field_name,
            )

            if not isinstance(value, str):
                raise ValueError(
                    f"El campo '{field_name}' debe contener texto."
                )

            normalized = value.strip()

            if not normalized:
                raise ValueError(
                    f"El campo '{field_name}' no puede estar vacío."
                )

            object.__setattr__(
                self,
                field_name,
                normalized,
            )


@dataclass(frozen=True, slots=True)
class NodeHealthPanelData:
    """Diagnóstico de salud integral preparado para el dashboard."""

    state: str
    system_state: str
    network_state: str

    interfaces: tuple[
        NodeHealthInterfaceRowData,
        ...,
    ]

    captured_at: datetime

    def __post_init__(self) -> None:
        for field_name in (
            "state",
            "system_state",
            "network_state",
        ):
            value = getattr(
                self,
                field_name,
            )

            if not isinstance(value, str):
                raise ValueError(
                    f"El campo '{field_name}' debe contener texto."
                )

            normalized = value.strip()

            if not normalized:
                raise ValueError(
                    f"El campo '{field_name}' no puede estar vacío."
                )

            object.__setattr__(
                self,
                field_name,
                normalized,
            )

        if not isinstance(
            self.interfaces,
            tuple,
        ):
            raise ValueError(
                "El campo 'interfaces' debe ser una tupla."
            )

        if not all(
            isinstance(
                item,
                NodeHealthInterfaceRowData,
            )
            for item in self.interfaces
        ):
            raise ValueError(
                "Todas las interfaces deben ser "
                "NodeHealthInterfaceRowData."
            )

        interface_names = tuple(
            item.interface
            for item in self.interfaces
        )

        if len(interface_names) != len(
            set(interface_names)
        ):
            raise ValueError(
                "No pueden existir interfaces duplicadas."
            )

        if not isinstance(
            self.captured_at,
            datetime,
        ):
            raise ValueError(
                "El campo 'captured_at' debe contener "
                "una fecha válida."
            )

        if self.captured_at.tzinfo is None:
            raise ValueError(
                "El campo 'captured_at' debe incluir zona horaria."
            )

    @property
    def interface_count(self) -> int:
        """Cantidad de interfaces incluidas en el diagnóstico."""

        return len(self.interfaces)

    @property
    def unhealthy_interfaces(
        self,
    ) -> tuple[NodeHealthInterfaceRowData, ...]:
        """Interfaces que requieren atención operacional."""

        return tuple(
            item
            for item in self.interfaces
            if item.state
            in {
                "WARNING",
                "DEGRADED",
                "CRITICAL",
            }
        )
