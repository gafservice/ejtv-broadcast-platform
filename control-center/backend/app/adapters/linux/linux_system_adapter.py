"""Implementación Linux del contrato SystemAdapter."""

import platform
import socket

from app.adapters.base.system_adapter import SystemAdapter


class LinuxSystemAdapter(SystemAdapter):
    """Obtiene información del sistema operativo Linux."""

    def hostname(self) -> str:
        """Retorna el nombre del equipo."""

        return socket.gethostname()

    def operating_system(self) -> str:
        """Retorna el nombre y la versión del sistema operativo."""

        try:
            os_release = platform.freedesktop_os_release()

            name = os_release.get("PRETTY_NAME")
            if name:
                return name

            system_name = os_release.get("NAME", "Linux")
            system_version = os_release.get("VERSION", "")

            return f"{system_name} {system_version}".strip()

        except OSError:
            return platform.platform()

    def kernel(self) -> str:
        """Retorna la versión del kernel."""

        return platform.release()
