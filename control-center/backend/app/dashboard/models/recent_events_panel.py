"""Modelos de presentación para eventos recientes del NOC."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class RecentEventRowData:
    """Evento operacional preparado para presentación."""

    event_id: str
    event_type: str
    severity: str
    title: str
    occurred_at: datetime

    def __post_init__(self) -> None:
        for field_name in (
            "event_id",
            "event_type",
            "severity",
            "title",
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
            self.occurred_at,
            datetime,
        ):
            raise ValueError(
                "El campo 'occurred_at' debe contener "
                "una fecha válida."
            )

        if self.occurred_at.tzinfo is None:
            raise ValueError(
                "El campo 'occurred_at' debe incluir "
                "zona horaria."
            )


@dataclass(frozen=True, slots=True)
class RecentEventsPanelData:
    """Colección de eventos recientes preparada para el dashboard."""

    events: tuple[RecentEventRowData, ...]

    def __post_init__(self) -> None:
        if not isinstance(
            self.events,
            tuple,
        ):
            raise ValueError(
                "El campo 'events' debe ser una tupla."
            )

        if not all(
            isinstance(
                event,
                RecentEventRowData,
            )
            for event in self.events
        ):
            raise ValueError(
                "Todos los eventos deben ser "
                "RecentEventRowData."
            )

        event_ids = tuple(
            event.event_id
            for event in self.events
        )

        if len(event_ids) != len(
            set(event_ids)
        ):
            raise ValueError(
                "No pueden existir event_id duplicados."
            )

    @property
    def event_count(self) -> int:
        """Cantidad de eventos incluidos en el panel."""

        return len(self.events)

    @property
    def is_empty(self) -> bool:
        """Indica si el panel no contiene eventos."""

        return not self.events
