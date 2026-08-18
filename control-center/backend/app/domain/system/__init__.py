"""Modelos del dominio relacionados con el sistema."""

from app.domain.system.models import (
    CPUInfo,
    DiskInfo,
    MemoryInfo,
    NetworkInfo,
    SystemInfo,
    SystemResources,
    UptimeInfo,
)

from app.domain.system.network_interfaces import (
    NetworkInterfaceInfo,
    NetworkInterfaceType,
)

from app.domain.system.network_rates import (
    MultiNetworkRateCalculator,
    NetworkRate,
    NetworkRateCalculator,
)

from app.domain.system.network_telemetry import (
    NetworkInterfaceTelemetry,
)


from app.domain.system.services import (
    MonitoredService,
    ServiceInstance,
    ServiceMonitoringSnapshot,
    ServiceStatus,
)

__all__ = [
    "CPUInfo",
    "DiskInfo",
    "MemoryInfo",
    "NetworkInfo",
    "NetworkInterfaceInfo",
    "NetworkInterfaceType",
    "MultiNetworkRateCalculator",
    "NetworkRate",
    "NetworkRateCalculator",
    "NetworkInterfaceTelemetry",
    "SystemInfo",
    "SystemResources",
    "UptimeInfo",
    "MonitoredService",
    "ServiceInstance",
    "ServiceMonitoringSnapshot",
    "ServiceStatus",
]
