from datetime import UTC, datetime

from rich.console import Console

from app.dashboard.models.capacity_panel import (
    CapacityPanelData,
    CapacityResourceRowData,
)
from app.dashboard.renderers.capacity_panel_renderer import (
    CapacityPanelRenderer,
)
from app.noc.domain.node_capacity import (
    CapacityResource,
    NodeCapacity,
)


CAPTURED_AT = datetime(
    2026,
    10,
    2,
    12,
    0,
    tzinfo=UTC,
)


def _capacity() -> NodeCapacity:
    return NodeCapacity(
        resources=(
            CapacityResource(
                resource="System Memory",
                maximum=8_000_000_000,
                allocated=3_000_000_000,
                reserved=0,
                available=5_000_000_000,
                unit="bytes",
            ),
            CapacityResource(
                resource="Streaming Channels",
                maximum=16,
                allocated=10,
                reserved=2,
                available=4,
                unit="channels",
            ),
        ),
    )


def test_capacity_panel_data_projects_canonical_resources() -> None:
    data = CapacityPanelData.from_capacity(
        _capacity(),
        captured_at=CAPTURED_AT,
    )

    assert data.captured_at == CAPTURED_AT
    assert len(data.resources) == 2

    memory = data.resources[0]

    assert isinstance(memory, CapacityResourceRowData)
    assert memory.resource == "System Memory"
    assert memory.maximum == 8_000_000_000
    assert memory.allocated == 3_000_000_000
    assert memory.reserved == 0
    assert memory.available == 5_000_000_000
    assert memory.unit == "bytes"
    assert memory.utilization_percent == 37.5


def test_capacity_panel_is_generic_for_non_host_resources() -> None:
    data = CapacityPanelData.from_capacity(
        _capacity(),
        captured_at=CAPTURED_AT,
    )

    channels = data.resources[1]

    assert channels.resource == "Streaming Channels"
    assert channels.maximum == 16
    assert channels.allocated == 10
    assert channels.reserved == 2
    assert channels.available == 4
    assert channels.unit == "channels"
    assert channels.utilization_percent == 62.5


def test_capacity_panel_renderer_uses_capacity_semantics() -> None:
    data = CapacityPanelData.from_capacity(
        _capacity(),
        captured_at=CAPTURED_AT,
    )

    console = Console(
        record=True,
        width=120,
        color_system=None,
    )

    console.print(
        CapacityPanelRenderer().render(data)
    )

    output = console.export_text()

    assert "CAPACITY" in output
    assert "System Memory" in output
    assert "Streaming Channels" in output
    assert "37.5%" in output
    assert "62.5%" in output


def test_capacity_projection_preserves_canonical_values() -> None:
    capacity = _capacity()

    data = CapacityPanelData.from_capacity(
        capacity,
        captured_at=CAPTURED_AT,
    )

    for source, projected in zip(
        capacity.resources,
        data.resources,
        strict=True,
    ):
        assert projected.resource == source.resource
        assert projected.maximum == source.maximum
        assert projected.allocated == source.allocated
        assert projected.reserved == source.reserved
        assert projected.available == source.available
        assert projected.unit == source.unit
        assert (
            projected.utilization_percent
            == source.utilization_percent
        )
