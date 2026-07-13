"""Construcción de dependencias utilizadas por la API."""

from functools import lru_cache

from app.adapters.linux.linux_system_adapter import LinuxSystemAdapter
from app.services.system_service import SystemService


@lru_cache
def get_system_service() -> SystemService:
    """Construye el servicio de sistema para el entorno actual."""

    adapter = LinuxSystemAdapter()
    return SystemService(adapter)
