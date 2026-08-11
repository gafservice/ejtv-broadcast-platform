"""Tests for NodeInfo.

ENG-013B — Node SDK
NCS reference: 10-NODE-INFO.md
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.noc.domain.node_info import NodeInfo
from app.noc.domain.node_instance import NodeInstanceId


def make_node_info() -> NodeInfo:
    return NodeInfo(
        instance_id=NodeInstanceId("streaming-primary"),
        hostname="broadcast-node-01",
        fqdn="broadcast-node-01.company.local",
        platform="Bare Metal",
        operating_system="Ubuntu Server 24.04 LTS",
        architecture="x86_64",
        runtime="Python 3.13",
        location="San Jose",
        boot_time=datetime.now(timezone.utc) - timedelta(hours=2),
        metadata={
            "cluster": "noc-primary",
            "zone": "dc-01",
        },
    )


def test_node_info_can_be_created() -> None:
    info = make_node_info()

    assert info.instance_id == NodeInstanceId(
        "streaming-primary"
    )
    assert info.hostname == "broadcast-node-01"
    assert info.platform == "Bare Metal"
    assert info.operating_system == "Ubuntu Server 24.04 LTS"
    assert info.architecture == "x86_64"
    assert info.runtime == "Python 3.13"


@pytest.mark.parametrize(
    "field",
    [
        "hostname",
        "platform",
        "operating_system",
        "architecture",
        "runtime",
    ],
)
def test_node_info_rejects_empty_required_strings(
    field: str,
) -> None:
    values = {
        "instance_id": NodeInstanceId("streaming-primary"),
        "hostname": "broadcast-node-01",
        "platform": "Bare Metal",
        "operating_system": "Ubuntu Server",
        "architecture": "x86_64",
        "runtime": "Python 3.13",
        "boot_time": datetime.now(timezone.utc),
    }

    values[field] = "   "

    with pytest.raises(ValueError):
        NodeInfo(**values)


def test_node_info_normalizes_strings() -> None:
    info = NodeInfo(
        instance_id=NodeInstanceId("streaming-primary"),
        hostname="  broadcast-node-01  ",
        fqdn="  broadcast-node-01.company.local  ",
        platform="  Bare Metal  ",
        operating_system="  Ubuntu Server  ",
        architecture="  x86_64  ",
        runtime="  Python 3.13  ",
        location="  San Jose  ",
        boot_time=datetime.now(timezone.utc),
    )

    assert info.hostname == "broadcast-node-01"
    assert info.fqdn == "broadcast-node-01.company.local"
    assert info.platform == "Bare Metal"
    assert info.operating_system == "Ubuntu Server"
    assert info.architecture == "x86_64"
    assert info.runtime == "Python 3.13"
    assert info.location == "San Jose"


def test_node_info_empty_optional_strings_become_none() -> None:
    info = NodeInfo(
        instance_id=NodeInstanceId("streaming-primary"),
        hostname="broadcast-node-01",
        fqdn="   ",
        platform="Bare Metal",
        operating_system="Ubuntu Server",
        architecture="x86_64",
        runtime="Python 3.13",
        location="   ",
        boot_time=datetime.now(timezone.utc),
    )

    assert info.fqdn is None
    assert info.location is None


def test_node_info_rejects_invalid_instance_id_type() -> None:
    with pytest.raises(TypeError):
        NodeInfo(
            instance_id="streaming-primary",  # type: ignore[arg-type]
            hostname="broadcast-node-01",
            platform="Bare Metal",
            operating_system="Ubuntu Server",
            architecture="x86_64",
            runtime="Python 3.13",
            boot_time=datetime.now(timezone.utc),
        )


def test_node_info_rejects_naive_boot_time() -> None:
    with pytest.raises(ValueError):
        NodeInfo(
            instance_id=NodeInstanceId("streaming-primary"),
            hostname="broadcast-node-01",
            platform="Bare Metal",
            operating_system="Ubuntu Server",
            architecture="x86_64",
            runtime="Python 3.13",
            boot_time=datetime(2026, 8, 11, 18, 0),
        )


def test_node_info_rejects_non_utc_boot_time() -> None:
    non_utc = timezone(timedelta(hours=-6))

    with pytest.raises(ValueError):
        NodeInfo(
            instance_id=NodeInstanceId("streaming-primary"),
            hostname="broadcast-node-01",
            platform="Bare Metal",
            operating_system="Ubuntu Server",
            architecture="x86_64",
            runtime="Python 3.13",
            boot_time=datetime(
                2026,
                8,
                11,
                13,
                0,
                tzinfo=non_utc,
            ),
        )


def test_node_info_reports_uptime() -> None:
    info = NodeInfo(
        instance_id=NodeInstanceId("streaming-primary"),
        hostname="broadcast-node-01",
        platform="Bare Metal",
        operating_system="Ubuntu Server",
        architecture="x86_64",
        runtime="Python 3.13",
        boot_time=datetime.now(timezone.utc) - timedelta(hours=2),
    )

    assert info.uptime >= timedelta(hours=1, minutes=59)


def test_node_info_future_boot_time_returns_zero_uptime() -> None:
    info = NodeInfo(
        instance_id=NodeInstanceId("streaming-primary"),
        hostname="broadcast-node-01",
        platform="Bare Metal",
        operating_system="Ubuntu Server",
        architecture="x86_64",
        runtime="Python 3.13",
        boot_time=datetime.now(timezone.utc) + timedelta(hours=1),
    )

    assert info.uptime == timedelta(0)


def test_node_info_metadata_is_normalized() -> None:
    info = NodeInfo(
        instance_id=NodeInstanceId("streaming-primary"),
        hostname="broadcast-node-01",
        platform="Bare Metal",
        operating_system="Ubuntu Server",
        architecture="x86_64",
        runtime="Python 3.13",
        boot_time=datetime.now(timezone.utc),
        metadata={
            " cluster ": " noc-primary ",
        },
    )

    assert info.metadata == {
        "cluster": "noc-primary",
    }


def test_node_info_rejects_empty_metadata_key() -> None:
    with pytest.raises(ValueError):
        NodeInfo(
            instance_id=NodeInstanceId("streaming-primary"),
            hostname="broadcast-node-01",
            platform="Bare Metal",
            operating_system="Ubuntu Server",
            architecture="x86_64",
            runtime="Python 3.13",
            boot_time=datetime.now(timezone.utc),
            metadata={
                "   ": "value",
            },
        )


def test_node_info_rejects_non_string_metadata_value() -> None:
    with pytest.raises(TypeError):
        NodeInfo(
            instance_id=NodeInstanceId("streaming-primary"),
            hostname="broadcast-node-01",
            platform="Bare Metal",
            operating_system="Ubuntu Server",
            architecture="x86_64",
            runtime="Python 3.13",
            boot_time=datetime.now(timezone.utc),
            metadata={
                "cpu": 8,  # type: ignore[dict-item]
            },
        )


def test_node_info_is_immutable() -> None:
    info = make_node_info()

    with pytest.raises(AttributeError):
        info.hostname = "another-host"  # type: ignore[misc]


def test_node_info_string_representation_is_hostname() -> None:
    info = make_node_info()

    assert str(info) == "broadcast-node-01"
