"""Linux execution-environment information provider for the NOC.

ENG-013B — Node SDK

This infrastructure adapter observes the local Linux runtime and projects
that information into the canonical NodeInfo domain model.

It does not mutate Nodes, NodeInstances or repositories.
"""

from __future__ import annotations

import os
import platform
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path

import psutil

from app.noc.domain.node_info import NodeInfo
from app.noc.domain.node_instance import NodeInstanceId


class LinuxSystemInfoProvider:
    """Collect NodeInfo from the local Linux execution environment."""

    def collect(
        self,
        instance_id: NodeInstanceId,
    ) -> NodeInfo:
        """Return execution information for the local runtime."""

        if not isinstance(instance_id, NodeInstanceId):
            raise TypeError(
                "instance_id must be a NodeInstanceId"
            )

        hostname = socket.gethostname()

        return NodeInfo(
            instance_id=instance_id,
            hostname=hostname,
            fqdn=self._fqdn(hostname),
            platform=self._platform(),
            operating_system=self._operating_system(),
            architecture=platform.machine(),
            runtime=self._runtime(),
            boot_time=datetime.fromtimestamp(
                psutil.boot_time(),
                tz=timezone.utc,
            ),
            metadata=self._metadata(),
        )

    @staticmethod
    def _fqdn(hostname: str) -> str | None:
        value = socket.getfqdn(hostname).strip()

        if not value:
            return None

        return value

    @staticmethod
    def _platform() -> str:
        """Describe the execution platform conservatively."""

        if Path("/.dockerenv").exists():
            return "Container"

        if os.environ.get("container"):
            return "Container"

        return "Linux Host"

    @staticmethod
    def _operating_system() -> str:
        """Return the best available Linux distribution description."""

        try:
            os_release = platform.freedesktop_os_release()
        except OSError:
            os_release = {}

        pretty_name = os_release.get("PRETTY_NAME")

        if pretty_name:
            return pretty_name.strip()

        system = platform.system().strip()
        release = platform.release().strip()

        if system and release:
            return f"{system} {release}"

        return system or "Linux"

    @staticmethod
    def _runtime() -> str:
        implementation = platform.python_implementation()
        version = platform.python_version()

        return f"{implementation} {version}"

    @staticmethod
    def _metadata() -> dict[str, str]:
        return {
            "kernel": platform.release(),
            "python_executable": sys.executable,
        }
