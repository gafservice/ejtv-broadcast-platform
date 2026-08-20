"""Tests de los modelos del panel NODE HEALTH."""

from datetime import UTC, datetime

import pytest

from app.dashboard.models import (
    NodeHealthInterfaceRowData,
    NodeHealthPanelData,
)


CAPTURED_AT = datetime(
    2026,
    8,
    18,
    23,
    30,
    tzinfo=UTC,
)


def make_row(
    interface: str = "ens2f0",
    *,
    state: str = "WARNING",
) -> NodeHealthInterfaceRowData:
    return NodeHealthInterfaceRowData(
        interface=interface,
        state=state,
        reason="Elevated network error or drop rate",
    )


def make_panel(
    **overrides,
) -> NodeHealthPanelData:
    values = {
        "state": "WARNING",
        "system_state": "HEALTHY",
        "network_state": "WARNING",
        "interfaces": (
            make_row(),
        ),
        "captured_at": CAPTURED_AT,
    }

    values.update(overrides)

    return NodeHealthPanelData(
        **values
    )


def test_row_creation() -> None:
    row = make_row()

    assert row.interface == "ens2f0"
    assert row.state == "WARNING"


def test_row_normalizes_text() -> None:
    row = NodeHealthInterfaceRowData(
        interface="  ens2f0  ",
        state="  WARNING  ",
        reason="  Test reason  ",
    )

    assert row.interface == "ens2f0"
    assert row.state == "WARNING"
    assert row.reason == "Test reason"


@pytest.mark.parametrize(
    "field",
    (
        "interface",
        "state",
        "reason",
    ),
)
def test_row_rejects_empty_text(
    field: str,
) -> None:
    values = {
        "interface": "ens2f0",
        "state": "HEALTHY",
        "reason": "OK",
    }

    values[field] = "   "

    with pytest.raises(ValueError):
        NodeHealthInterfaceRowData(
            **values
        )


def test_panel_creation() -> None:
    panel = make_panel()

    assert panel.state == "WARNING"
    assert panel.system_state == "HEALTHY"
    assert panel.network_state == "WARNING"
    assert panel.interface_count == 1


def test_panel_returns_unhealthy_interfaces() -> None:
    panel = make_panel(
        interfaces=(
            make_row(
                "enp9s0",
                state="HEALTHY",
            ),
            make_row(
                "ens2f0",
                state="WARNING",
            ),
            make_row(
                "ens2f1",
                state="CRITICAL",
            ),
        )
    )

    assert tuple(
        item.interface
        for item in panel.unhealthy_interfaces
    ) == (
        "ens2f0",
        "ens2f1",
    )


def test_panel_accepts_empty_interfaces() -> None:
    panel = make_panel(
        interfaces=(),
    )

    assert panel.interface_count == 0


def test_panel_rejects_duplicate_interfaces() -> None:
    with pytest.raises(ValueError):
        make_panel(
            interfaces=(
                make_row("ens2f0"),
                make_row("ens2f0"),
            )
        )


def test_panel_rejects_non_tuple_interfaces() -> None:
    with pytest.raises(ValueError):
        make_panel(
            interfaces=[],  # type: ignore[arg-type]
        )


def test_panel_rejects_naive_timestamp() -> None:
    with pytest.raises(ValueError):
        make_panel(
            captured_at=datetime(
                2026,
                8,
                18,
                23,
                30,
            )
        )


def test_interface_row_accepts_quality_rates() -> None:
    row = NodeHealthInterfaceRowData(
        interface="enp9s0",
        state="WARNING",
        reason="Elevated network error or drop rate",
        error_rate=0.25,
        drop_rate=1.50,
    )

    assert row.error_rate == 0.25
    assert row.drop_rate == 1.50


@pytest.mark.parametrize(
    "field_name",
    (
        "error_rate",
        "drop_rate",
    ),
)
def test_interface_row_rejects_negative_quality_rate(
    field_name: str,
) -> None:
    kwargs = {
        "interface": "enp9s0",
        "state": "WARNING",
        "reason": "Elevated network error or drop rate",
        "error_rate": 0.0,
        "drop_rate": 0.0,
    }

    kwargs[field_name] = -1.0

    with pytest.raises(ValueError):
        NodeHealthInterfaceRowData(**kwargs)


@pytest.mark.parametrize(
    "field_name",
    (
        "error_rate",
        "drop_rate",
    ),
)
def test_interface_row_rejects_non_numeric_quality_rate(
    field_name: str,
) -> None:
    kwargs = {
        "interface": "enp9s0",
        "state": "WARNING",
        "reason": "Elevated network error or drop rate",
        "error_rate": 0.0,
        "drop_rate": 0.0,
    }

    kwargs[field_name] = "invalid"

    with pytest.raises(ValueError):
        NodeHealthInterfaceRowData(**kwargs)
