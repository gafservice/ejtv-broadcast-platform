"""Contrato para consultar la identidad básica de un sistema."""

from abc import ABC, abstractmethod


class SystemAdapter(ABC):
    """Contrato de acceso a información básica del sistema."""

    @abstractmethod
    def hostname(self) -> str:
        """Retorna el nombre del equipo."""

    @abstractmethod
    def operating_system(self) -> str:
        """Retorna el nombre y versión del sistema operativo."""

    @abstractmethod
    def kernel(self) -> str:
        """Retorna la versión del kernel."""
