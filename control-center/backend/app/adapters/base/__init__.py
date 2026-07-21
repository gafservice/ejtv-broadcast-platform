"""Contratos base para adaptadores de infraestructura."""

from .resource_adapter import ResourceAdapter
from .system_adapter import SystemAdapter

__all__ = [
    "ResourceAdapter",
    "SystemAdapter",
]
