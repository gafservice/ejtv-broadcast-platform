"""
Servicio coordinador para construir snapshots completos del dashboard.

Este módulo centraliza la creación de DashboardData y mantiene fuera de
los endpoints HTTP la lógica de coordinación entre mediciones, recursos
del sistema y modelos de presentación.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.dashboard.models import DashboardData
from app.dashboard.services.dashboard_service import DashboardService
from app.domain.sessions.measurement import SessionMeasurement
from app.domain.streaming import (
    MediaMTXSnapshot,
    StreamingHealth,
    StreamingMeasurement,
)
from app.domain.system import SystemResources


@dataclass(frozen=True, slots=True)
class DashboardSnapshotInput:
    """
    Datos necesarios para construir un snapshot completo del dashboard.

    Todos los valores representan una única captura lógica del estado
    de la plataforma.
    """

    hostname: str
    mediamtx_online: bool
    api_online: bool

    snapshot: MediaMTXSnapshot
    measurement: StreamingMeasurement

    session_measurement: SessionMeasurement | None = None
    system_resources: SystemResources | None = None
    previous_system_resources: SystemResources | None = None
    health: StreamingHealth | None = None


class DashboardSnapshotService:
    """
    Coordina la construcción del snapshot completo del dashboard.

    La obtención de datos permanece en los servicios y adaptadores
    especializados. Esta clase se encarga únicamente de reunir esos
    resultados mediante DashboardService.
    """

    def __init__(
        self,
        dashboard_service: DashboardService | None = None,
    ) -> None:
        """
        Inicializa el coordinador.

        Args:
            dashboard_service:
                Servicio encargado de transformar mediciones del dominio
                en modelos de presentación para el dashboard.
        """

        self._dashboard_service = (
            dashboard_service
            if dashboard_service is not None
            else DashboardService()
        )

    def build_snapshot(
        self,
        snapshot_input: DashboardSnapshotInput,
    ) -> DashboardData:
        """
        Construye un snapshot completo del dashboard.

        Args:
            snapshot_input:
                Conjunto de mediciones y estados correspondientes a la
                captura actual.

        Returns:
            DashboardData listo para ser utilizado por el dashboard Rich,
            la API HTTP u otro consumidor.

        Raises:
            ValueError:
                Cuando las mediciones no corresponden al mismo instante
                o contienen información inconsistente. La validación se
                delega a DashboardService.
        """

        return self._dashboard_service.build_dashboard_from_measurement(
            hostname=snapshot_input.hostname,
            mediamtx_online=snapshot_input.mediamtx_online,
            api_online=snapshot_input.api_online,
            snapshot=snapshot_input.snapshot,
            measurement=snapshot_input.measurement,
            session_measurement=snapshot_input.session_measurement,
            system_resources=snapshot_input.system_resources,
            previous_system_resources=(
                snapshot_input.previous_system_resources
            ),
            health=snapshot_input.health,
        )