"""Construcción de dependencias utilizadas por la API."""

from functools import lru_cache

from app.adapters.linux.linux_system_adapter import LinuxSystemAdapter
from app.dashboard.application import DashboardApplication
from app.dashboard.live_monitor import build_dashboard_application
from app.services.system_service import SystemService


@lru_cache
def get_system_service() -> SystemService:
    """Construye el servicio de sistema para el entorno actual."""

    adapter = LinuxSystemAdapter()
    return SystemService(adapter)


@lru_cache
def get_dashboard_application() -> DashboardApplication:
    """Construye la aplicación coordinadora del dashboard."""

    return build_dashboard_application()