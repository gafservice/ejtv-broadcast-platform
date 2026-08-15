"""Tests for LinuxSystemInfoProvider."""

from datetime import datetime, timezone

import pytest

from app.noc.domain.node_info import NodeInfo
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.infrastructure.system_info_provider import (
    LinuxSystemInfoProvider,
)


def test_provider_collects_node_info() -> None:
    provider = LinuxSystemInfoProvider()

    info = provider.collect(
        NodeInstanceId("streaming-primary")
    )

    assert isinstance(info, NodeInfo)
    assert info.instance_id == NodeInstanceId(
        "streaming-primary"
    )


def test_provider_collects_required_strings() -> None:
    provider = LinuxSystemInfoProvider()

    info = provider.collect(
        NodeInstanceId("streaming-primary")
    )

    assert info.hostname
    assert info.platform
    assert info.operating_system
    assert info.architecture
    assert info.runtime


def test_provider_collects_utc_boot_time() -> None:
    provider = LinuxSystemInfoProvider()

    info = provider.collect(
        NodeInstanceId("streaming-primary")
    )

    assert isinstance(info.boot_time, datetime)
    assert info.boot_time.tzinfo is not None
    assert info.boot_time.utcoffset() is not None
    assert info.boot_time.utcoffset().total_seconds() == 0


def test_provider_boot_time_is_not_in_future() -> None:
    provider = LinuxSystemInfoProvider()

    info = provider.collect(
        NodeInstanceId("streaming-primary")
    )

    assert info.boot_time <= datetime.now(timezone.utc)


def test_provider_reports_python_runtime() -> None:
    provider = LinuxSystemInfoProvider()

    info = provider.collect(
        NodeInstanceId("streaming-primary")
    )

    assert "Python" in info.runtime


def test_provider_reports_architecture() -> None:
    provider = LinuxSystemInfoProvider()

    info = provider.collect(
        NodeInstanceId("streaming-primary")
    )

    assert info.architecture.strip()


def test_provider_provides_metadata() -> None:
    provider = LinuxSystemInfoProvider()

    info = provider.collect(
        NodeInstanceId("streaming-primary")
    )

    assert info.metadata is not None
    assert "kernel" in info.metadata
    assert "python_executable" in info.metadata


def test_provider_rejects_invalid_instance_id() -> None:
    provider = LinuxSystemInfoProvider()

    with pytest.raises(TypeError):
        provider.collect(
            "streaming-primary"  # type: ignore[arg-type]
        )
