"""Implementación Linux del contrato SystemAdapter."""

import platform
import socket
import time

import psutil

from app.adapters.base.system_adapter import SystemAdapter
from app.domain.system import (
    CPUInfo,
    DiskInfo,
    MemoryInfo,
    UptimeInfo,
)


class LinuxSystemAdapter(SystemAdapter):
    """Obtiene información y recursos del sistema operativo Linux."""

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

    def cpu_info(self) -> CPUInfo:
        """Retorna el estado actual del procesador."""

        frequency = psutil.cpu_freq()

        frequency_mhz = (
            float(frequency.current)
            if frequency is not None
            else None
        )

        return CPUInfo(
            usage_percent=psutil.cpu_percent(interval=0.1),
            logical_cores=psutil.cpu_count(logical=True) or 1,
            physical_cores=psutil.cpu_count(logical=False),
            frequency_mhz=frequency_mhz,
        )

    def memory_info(self) -> MemoryInfo:
        """Retorna el estado actual de la memoria principal."""

        memory = psutil.virtual_memory()

        return MemoryInfo(
            total_bytes=int(memory.total),
            available_bytes=int(memory.available),
            used_bytes=int(memory.used),
            usage_percent=float(memory.percent),
        )

    def disk_info(self) -> DiskInfo:
        """Retorna el estado de la partición raíz."""

        disk = psutil.disk_usage("/")

        return DiskInfo(
            total_bytes=int(disk.total),
            used_bytes=int(disk.used),
            free_bytes=int(disk.free),
            usage_percent=float(disk.percent),
        )

    def uptime_info(self) -> UptimeInfo:
        """Retorna el tiempo de funcionamiento del sistema."""

        uptime_seconds = max(
            0,
            int(time.time() - psutil.boot_time()),
        )

        return UptimeInfo(
            uptime_seconds=uptime_seconds,
        )