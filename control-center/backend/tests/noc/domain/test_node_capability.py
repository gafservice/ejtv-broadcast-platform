"""Tests for NodeCapability.

ENG-013B — Node SDK
NCS reference: 14-NODE-CAPABILITY.md
"""

import pytest

from app.noc.domain.node_capability import (
    CapabilityCategory,
    CapabilityDefinition,
    NodeCapability,
)


def test_capability_category_contains_canonical_values() -> None:
    expected = {
        "PROTOCOL",
        "SECURITY",
        "PROCESSING",
        "STORAGE",
        "MONITORING",
        "AUTOMATION",
        "OTHER",
    }

    assert {
        category.value for category in CapabilityCategory
    } == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("protocol", CapabilityCategory.PROTOCOL),
        (" SECURITY ", CapabilityCategory.SECURITY),
        ("processing", CapabilityCategory.PROCESSING),
        ("storage", CapabilityCategory.STORAGE),
        ("monitoring", CapabilityCategory.MONITORING),
        ("automation", CapabilityCategory.AUTOMATION),
        ("other", CapabilityCategory.OTHER),
    ],
)
def test_capability_category_from_value(
    raw: str,
    expected: CapabilityCategory,
) -> None:
    assert CapabilityCategory.from_value(raw) is expected


def test_capability_category_rejects_unknown_value() -> None:
    with pytest.raises(ValueError):
        CapabilityCategory.from_value("NETWORKING")


def test_capability_category_rejects_empty_value() -> None:
    with pytest.raises(ValueError):
        CapabilityCategory.from_value("   ")


def test_capability_definition_can_be_created() -> None:
    capability = CapabilityDefinition(
        name="SRT",
        category=CapabilityCategory.PROTOCOL,
        version="1.0",
    )

    assert capability.name == "SRT"
    assert capability.enabled is True
    assert capability.version == "1.0"


def test_capability_definition_normalizes_name() -> None:
    capability = CapabilityDefinition(
        name="  webrtc  ",
        category=CapabilityCategory.PROTOCOL,
    )

    assert capability.name == "WEBRTC"


def test_capability_definition_rejects_empty_name() -> None:
    with pytest.raises(ValueError):
        CapabilityDefinition(
            name="   ",
            category=CapabilityCategory.PROTOCOL,
        )


def test_capability_definition_rejects_invalid_category() -> None:
    with pytest.raises(TypeError):
        CapabilityDefinition(
            name="SRT",
            category="PROTOCOL",  # type: ignore[arg-type]
        )


def test_capability_definition_is_immutable() -> None:
    capability = CapabilityDefinition(
        name="SRT",
        category=CapabilityCategory.PROTOCOL,
    )

    with pytest.raises(AttributeError):
        capability.name = "RTMP"  # type: ignore[misc]


def test_node_capability_can_be_empty() -> None:
    capability = NodeCapability()

    assert capability.capabilities == ()
    assert len(capability) == 0


def test_node_capability_accepts_multiple_capabilities() -> None:
    capability = NodeCapability(
        capabilities=(
            CapabilityDefinition(
                name="SRT",
                category=CapabilityCategory.PROTOCOL,
            ),
            CapabilityDefinition(
                name="HLS",
                category=CapabilityCategory.PROTOCOL,
            ),
        )
    )

    assert len(capability) == 2


def test_node_capability_rejects_duplicate_names() -> None:
    with pytest.raises(ValueError):
        NodeCapability(
            capabilities=(
                CapabilityDefinition(
                    name="SRT",
                    category=CapabilityCategory.PROTOCOL,
                ),
                CapabilityDefinition(
                    name="srt",
                    category=CapabilityCategory.PROTOCOL,
                ),
            )
        )


def test_node_capability_supports_enabled_capability() -> None:
    capability = NodeCapability(
        capabilities=(
            CapabilityDefinition(
                name="SRT",
                category=CapabilityCategory.PROTOCOL,
            ),
        )
    )

    assert capability.supports("srt") is True


def test_node_capability_does_not_support_disabled_capability() -> None:
    capability = NodeCapability(
        capabilities=(
            CapabilityDefinition(
                name="SRT",
                category=CapabilityCategory.PROTOCOL,
                enabled=False,
            ),
        )
    )

    assert capability.supports("SRT") is False


def test_node_capability_get_returns_definition() -> None:
    definition = CapabilityDefinition(
        name="WEBRTC",
        category=CapabilityCategory.PROTOCOL,
    )

    capability = NodeCapability(
        capabilities=(definition,)
    )

    assert capability.get("webrtc") is definition


def test_node_capability_get_unknown_returns_none() -> None:
    capability = NodeCapability()

    assert capability.get("SRT") is None


def test_node_capability_enabled_collection() -> None:
    capability = NodeCapability(
        capabilities=(
            CapabilityDefinition(
                name="SRT",
                category=CapabilityCategory.PROTOCOL,
            ),
            CapabilityDefinition(
                name="RTMP",
                category=CapabilityCategory.PROTOCOL,
                enabled=False,
            ),
        )
    )

    assert len(capability.enabled) == 1
    assert capability.enabled[0].name == "SRT"


def test_node_capability_disabled_collection() -> None:
    capability = NodeCapability(
        capabilities=(
            CapabilityDefinition(
                name="SRT",
                category=CapabilityCategory.PROTOCOL,
            ),
            CapabilityDefinition(
                name="RTMP",
                category=CapabilityCategory.PROTOCOL,
                enabled=False,
            ),
        )
    )

    assert len(capability.disabled) == 1
    assert capability.disabled[0].name == "RTMP"


def test_node_capability_contains_enabled_capability() -> None:
    capability = NodeCapability(
        capabilities=(
            CapabilityDefinition(
                name="HLS",
                category=CapabilityCategory.PROTOCOL,
            ),
        )
    )

    assert "HLS" in capability
    assert "hls" in capability
    assert "SRT" not in capability
