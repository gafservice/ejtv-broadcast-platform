"""Modelos de presentación para alarmas operacionales activas del NOC."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ActiveAlarmRowData:
    """Alarma operacional preparada para presentación."""

    alarm_id: str
    alarm_type: str
    severity: str
    state: str
    message: str
    opened_at: datetime
    remote_address: str = "-"
    path: str = "-"
    protocol: str = "-"
    role: str = "-"

    def __post_init__(self) -> None:

        for field_name in (
            "alarm_id",
            "alarm_type",
            "severity",
            "state",
            "message",
            "remote_address",
            "path",
            "protocol",
            "role",
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
            self.opened_at,
            datetime,
        ):
            raise ValueError(
                "El campo 'opened_at' debe contener "
                "una fecha válida."
            )

        if self.opened_at.tzinfo is None:
            raise ValueError(
                "El campo 'opened_at' debe incluir "
                "zona horaria."
            )


@dataclass(frozen=True, slots=True)
class ActiveAlarmsPanelData:
    """Colección de alarmas activas preparada para el dashboard."""

    alarms: tuple[ActiveAlarmRowData, ...]
    total_items: int | None = None

    def __post_init__(self) -> None:
        if self.total_items is not None:
            if (
                isinstance(self.total_items, bool)
                or not isinstance(self.total_items, int)
            ):
                raise TypeError(
                    "total_items must be an int or None"
                )

            if self.total_items < 0:
                raise ValueError(
                    "total_items must be greater than or equal to zero"
                )

        if not isinstance(
            self.alarms,
            tuple,
        ):
            raise ValueError(
                "El campo 'alarms' debe ser una tupla."
            )

        if not all(
            isinstance(
                alarm,
                ActiveAlarmRowData,
            )
            for alarm in self.alarms
        ):
            raise ValueError(
                "Todas las alarmas deben ser "
                "ActiveAlarmRowData."
            )

        alarm_ids = tuple(
            alarm.alarm_id
            for alarm in self.alarms
        )

        if len(alarm_ids) != len(
            set(alarm_ids)
        ):
            raise ValueError(
                "No pueden existir alarm_id duplicados."
            )

    @property
    def alarm_count(self) -> int:
        """Cantidad de alarmas incluidas en el panel."""

        return len(self.alarms)

    @property
    def is_empty(self) -> bool:
        """Indica si no existen alarmas activas."""

        return not self.alarms
