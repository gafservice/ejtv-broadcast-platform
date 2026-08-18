"""Implementación Linux del contrato SystemAdapter."""

import platform
import socket
import time
from pathlib import Path

import psutil

import subprocess
from datetime import UTC, datetime

from app.adapters.base.system_adapter import SystemAdapter
from app.domain.system import (
    CPUInfo,
    DiskInfo,
    MemoryInfo,
    NetworkInfo,
    NetworkInterfaceInfo,
    NetworkInterfaceType,
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
        """Obtiene la utilización y características del procesador."""

        usage_percent = psutil.cpu_percent(
            interval=0.1,
        )

        per_core_usage_percent = psutil.cpu_percent(
            interval=0.1,
            percpu=True,
        )

        logical_cores = psutil.cpu_count(logical=True) or 1
        physical_cores = psutil.cpu_count(logical=False)
        frequency = psutil.cpu_freq()

        return CPUInfo(
            usage_percent=usage_percent,
            logical_cores=logical_cores,
            physical_cores=physical_cores,
            frequency_mhz=(
                frequency.current
                if frequency is not None
                else None
            ),
            per_core_usage_percent=tuple(
                per_core_usage_percent
            ),
        )

    def memory_info(self) -> MemoryInfo:
    
        memory = psutil.virtual_memory()

        return MemoryInfo(
            total_bytes=memory.total,
            available_bytes=memory.available,
            used_bytes=memory.used,
            usage_percent=memory.percent,
            free_bytes=memory.free,
            cached_bytes=memory.cached,
            buffers_bytes=memory.buffers,
        )

    def disk_info(self) -> DiskInfo:
        mount_point = "/"
        disk = psutil.disk_usage(mount_point)
        partitions = psutil.disk_partitions(all=False)

        root_partition = next(
            (
                partition
                for partition in partitions
                if partition.mountpoint == mount_point
            ),
            None,
        )

        device = (
            root_partition.device
            if root_partition is not None
            else "unknown"
        )

        filesystem_type = (
            root_partition.fstype
            if root_partition is not None
            else "unknown"
        )

        return DiskInfo(
            total_bytes=int(disk.total),
            used_bytes=int(disk.used),
            free_bytes=int(disk.free),
            usage_percent=float(disk.percent),
            device=device,
            mount_point=mount_point,
            filesystem_type=filesystem_type,
        )

        
    def network_info(self, interface: str) -> NetworkInfo:
        """Retorna los contadores acumulados de una interfaz de red."""

        if not isinstance(interface, str):
            raise TypeError(
                "El nombre de la interfaz debe ser una cadena."
            )

        normalized_interface = interface.strip()

        if not normalized_interface:
            raise ValueError(
                "El nombre de la interfaz no puede estar vacío."
            )

        counters_by_interface = psutil.net_io_counters(
            pernic=True,
        )

        counters = counters_by_interface.get(
            normalized_interface,
        )

        if counters is None:
            raise ValueError(
                f"La interfaz '{normalized_interface}' no existe."
            )

        return NetworkInfo(
            interface=normalized_interface,
            bytes_sent=int(counters.bytes_sent),
            bytes_received=int(counters.bytes_recv),
            packets_sent=int(counters.packets_sent),
            packets_received=int(counters.packets_recv),
            errors_in=int(counters.errin),
            errors_out=int(counters.errout),
            dropped_in=int(counters.dropin),
            dropped_out=int(counters.dropout),
        )
    def network_interface_info(
        self,
        interface: str,
    ) -> NetworkInterfaceInfo:
        """Obtiene identidad, clasificación y estado de una interfaz."""

        if not isinstance(interface, str):
            raise TypeError(
                "El nombre de la interfaz debe ser una cadena."
            )

        normalized_interface = interface.strip()

        if not normalized_interface:
            raise ValueError(
                "El nombre de la interfaz no puede estar vacío."
            )

        stats_by_interface = psutil.net_if_stats()
        addresses_by_interface = psutil.net_if_addrs()

        stats = stats_by_interface.get(
            normalized_interface
        )

        if stats is None:
            raise ValueError(
                f"La interfaz '{normalized_interface}' no existe."
            )

        addresses = addresses_by_interface.get(
            normalized_interface,
            (),
        )

        sysfs_path = (
            Path("/sys/class/net")
            / normalized_interface
        )

        interface_type = self._classify_network_interface(
            normalized_interface,
            sysfs_path,
        )

        carrier = self._read_carrier(
            sysfs_path
        )

        mac_address = None
        ipv4_addresses: list[str] = []
        ipv6_addresses: list[str] = []

        for address in addresses:
            if address.family == socket.AF_INET:
                ipv4_addresses.append(
                    address.address
                )

            elif address.family == socket.AF_INET6:
                ipv6_addresses.append(
                    address.address.split("%", 1)[0]
                )

            elif address.family == psutil.AF_LINK:
                mac_address = address.address

        duplex = self._normalize_duplex(
            stats.duplex
        )

        link_speed_mbps = (
            int(stats.speed)
            if stats.speed is not None
            and stats.speed > 0
            else None
        )

        return NetworkInterfaceInfo(
            interface=normalized_interface,
            interface_type=interface_type,
            is_up=bool(stats.isup),
            carrier=carrier,
            mtu=int(stats.mtu),
            mac_address=mac_address,
            link_speed_mbps=link_speed_mbps,
            duplex=duplex,
            ipv4_addresses=tuple(
                ipv4_addresses
            ),
            ipv6_addresses=tuple(
                ipv6_addresses
            ),
        )

    @staticmethod
    def _classify_network_interface(
        interface: str,
        sysfs_path: Path,
    ) -> NetworkInterfaceType:
        """Clasifica una interfaz usando información del sistema."""

        if interface == "lo":
            return NetworkInterfaceType.LOOPBACK

        if (sysfs_path / "wireless").exists():
            return NetworkInterfaceType.WIFI

        if (sysfs_path / "bridge").exists():
            return NetworkInterfaceType.BRIDGE

        if (sysfs_path / "bonding").exists():
            return NetworkInterfaceType.BOND

        if not (sysfs_path / "device").exists():
            return NetworkInterfaceType.VIRTUAL

        return NetworkInterfaceType.ETHERNET

    @staticmethod
    def _read_carrier(
        sysfs_path: Path,
    ) -> bool | None:
        """Lee el estado físico del carrier cuando está disponible."""

        carrier_path = sysfs_path / "carrier"

        try:
            value = carrier_path.read_text().strip()
        except OSError:
            return None

        if value == "1":
            return True

        if value == "0":
            return False

        return None

    @staticmethod
    def _normalize_duplex(
        duplex: int,
    ) -> str | None:
        """Convierte las constantes psutil de dúplex al dominio."""

        if duplex == psutil.NIC_DUPLEX_FULL:
            return "full"

        if duplex == psutil.NIC_DUPLEX_HALF:
            return "half"

        return None

    def network_interface_infos(
        self,
    ) -> tuple[NetworkInterfaceInfo, ...]:
        """Descubre identidad y estado de todas las interfaces."""

        interface_names = sorted(
            psutil.net_if_stats().keys()
        )

        return tuple(
            self.network_interface_info(
                interface
            )
            for interface in interface_names
        )

    def network_interfaces(self) -> tuple[NetworkInfo, ...]:
        """Descubre los contadores de todas las interfaces de red."""

        counters_by_interface = psutil.net_io_counters(
            pernic=True,
        )

        return tuple(
            NetworkInfo(
                interface=interface,
                bytes_sent=int(counters.bytes_sent),
                bytes_received=int(counters.bytes_recv),
                packets_sent=int(counters.packets_sent),
                packets_received=int(counters.packets_recv),
                errors_in=int(counters.errin),
                errors_out=int(counters.errout),
                dropped_in=int(counters.dropin),
                dropped_out=int(counters.dropout),
            )
            for interface, counters
            in sorted(counters_by_interface.items())
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
