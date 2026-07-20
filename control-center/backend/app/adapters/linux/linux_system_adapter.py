"""Implementación Linux del contrato SystemAdapter."""

import platform
import socket
import time

import psutil

import subprocess
from datetime import UTC, datetime

from app.adapters.base.system_adapter import SystemAdapter
from app.domain.system import (
    CPUInfo,
    DiskInfo,
    MemoryInfo,
    UptimeInfo,
    MonitoredService,
    ServiceInstance,
    ServiceMonitoringSnapshot,
    ServiceStatus,
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

    def service_monitoring(self) -> ServiceMonitoringSnapshot:
        """Retorna el estado de los servicios monitoreados."""

        services = (
            self._systemd_service(
                name="MediaMTX",
                unit="mediamtx.service",
            ),
            self._process_service(
                name="FFmpeg",
                process_name="ffmpeg",
            ),
            self._process_service(
                name="Control Center Backend",
                process_name="uvicorn",
            ),
        )

        return ServiceMonitoringSnapshot(
            services=services,
            captured_at=datetime.now(UTC),
        )

    def _systemd_service(
        self,
        name: str,
        unit: str,
    ) -> MonitoredService:
        """Obtiene el estado de una unidad systemd."""

        result = subprocess.run(
            [
                "systemctl",
                "show",
                unit,
                "--property=ActiveState",
                "--property=SubState",
                "--property=MainPID",
                "--no-pager",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        properties: dict[str, str] = {}

        for line in result.stdout.splitlines():
            key, separator, value = line.partition("=")

            if separator:
                properties[key] = value

        active_state = properties.get("ActiveState", "unknown")
        sub_state = properties.get("SubState", "unknown")

        status = self._map_systemd_status(
            active_state=active_state,
            sub_state=sub_state,
        )

        pid_text = properties.get("MainPID", "0")
        pid = int(pid_text) if pid_text.isdigit() else 0

        instances = (
            (self._process_instance(pid),)
            if pid > 0 and psutil.pid_exists(pid)
            else ()
        )

        return MonitoredService(
            name=name,
            identifier=unit,
            monitor_type="systemd",
            status=status,
            instances=instances,
        )

    def _process_service(
        self,
        name: str,
        process_name: str,
    ) -> MonitoredService:
        """Obtiene las instancias activas de un proceso."""

        instances: list[ServiceInstance] = []

        for process in psutil.process_iter(
            attrs=["pid", "name", "cmdline"],
        ):
            try:
                process_name_value = process.info.get("name") or ""
                command_line = process.info.get("cmdline") or []

                matches_name = process_name_value == process_name
                matches_command = any(
                    process_name in argument
                    for argument in command_line
                )

                if matches_name or matches_command:
                    instances.append(
                        self._process_instance(process.info["pid"])
                    )

            except (
                psutil.AccessDenied,
                psutil.NoSuchProcess,
                psutil.ZombieProcess,
            ):
                continue

        status = (
            ServiceStatus.RUNNING
            if instances
            else ServiceStatus.STOPPED
        )

        return MonitoredService(
            name=name,
            identifier=process_name,
            monitor_type="process",
            status=status,
            instances=tuple(instances),
        )

    def _process_instance(self, pid: int) -> ServiceInstance:
        """Obtiene métricas de una instancia de proceso."""

        process = psutil.Process(pid)

        uptime_seconds = max(
            0,
            int(time.time() - process.create_time()),
        )

        return ServiceInstance(
            pid=pid,
            cpu_percent=process.cpu_percent(interval=0.05),
            memory_bytes=process.memory_info().rss,
            uptime_seconds=uptime_seconds,
        )

    @staticmethod
    def _map_systemd_status(
        active_state: str,
        sub_state: str,
    ) -> ServiceStatus:
        """Convierte estados de systemd al dominio."""

        if active_state == "active" and sub_state == "running":
            return ServiceStatus.RUNNING

        if active_state == "failed":
            return ServiceStatus.FAILED

        if active_state == "inactive":
            return ServiceStatus.STOPPED

        return ServiceStatus.UNKNOWN      