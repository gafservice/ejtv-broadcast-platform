"""Tests for startup behavior of the owned NOC runtime."""

from __future__ import annotations

import asyncio
from datetime import timedelta
from unittest.mock import AsyncMock, Mock, patch

from app.main import _owned_noc_runtime
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId


def test_owned_runtime_catches_up_mature_history_before_background_loop(
) -> None:
    """Startup finalizes mature history before periodic maintenance."""

    asyncio.run(
        _exercise_owned_runtime_startup()
    )


async def _exercise_owned_runtime_startup() -> None:
    node_id = NodeId.create(
        id="streaming-core",
        name="streaming",
        display_name="Streaming Core",
    )
    instance_id = NodeInstanceId(
        "streaming-primary"
    )
    registry = Mock()

    managed_history_bootstrap = Mock()
    continuity = Mock()
    alarm_recovery = Mock()
    reconciliation = Mock()
    daily_history = Mock()

    daily_history.catch_up_mature_days = Mock()
    daily_history.run_forever = AsyncMock()

    telemetry = Mock()
    telemetry.run_forever = AsyncMock()

    session_observation = Mock()
    session_observation.run_forever = AsyncMock()

    call_order: list[str] = []

    managed_history_bootstrap.ensure_anchor.side_effect = (
        lambda **_: call_order.append(
            "managed-history-anchor"
        )
    )

    continuity.catch_up.side_effect = (
        lambda **_: call_order.append(
            "continuity"
        )
    )

    alarm_recovery.recover.side_effect = (
        lambda **_: call_order.append(
            "alarm-recovery"
        )
    )

    reconciliation.reconcile_between.side_effect = (
        lambda **_: call_order.append(
            "recent-reconciliation"
        )
    )

    daily_history.catch_up_mature_days.side_effect = (
        lambda **_: call_order.append(
            "mature-catch-up"
        )
    )

    async def history_forever(**_: object) -> None:
        call_order.append(
            "history-run-forever"
        )

    daily_history.run_forever.side_effect = (
        history_forever
    )

    with (
        patch(
            "app.main.get_managed_history_bootstrap_service",
            return_value=managed_history_bootstrap,
        ),
        patch(
            "app.main.get_daily_alarm_continuity_service",
            return_value=continuity,
        ),
        patch(
            "app.main.get_alarm_recovery_service",
            return_value=alarm_recovery,
        ),
        patch(
            "app.main.get_evidence_reconciliation_service",
            return_value=reconciliation,
        ),
        patch(
            "app.main.get_daily_history_maintenance_runtime",
            return_value=daily_history,
        ),
        patch(
            "app.main.get_telemetry_observation_runtime",
            return_value=telemetry,
        ),
        patch(
            "app.main.get_session_observation_runtime",
            return_value=session_observation,
        ),
        patch(
            "app.main.initialize_noc_runtime_info",
        ),
        patch(
            "app.main.initialize_noc_runtime_capacity",
        ),
        patch(
            "app.main.get_system_service",
        ),
        patch(
            "app.main.get_capacity_service",
        ),
    ):
        async with _owned_noc_runtime(
            node_id=node_id,
            node_instance_id=instance_id,
            registry=registry,
        ):
            assert (
                "mature-catch-up"
                in call_order
            )

    assert (
        call_order.index("managed-history-anchor")
        < call_order.index("continuity")
    )

    assert (
        call_order.index("continuity")
        < call_order.index("alarm-recovery")
    )

    assert (
        call_order.index("alarm-recovery")
        < call_order.index("recent-reconciliation")
    )

    assert (
        call_order.index("recent-reconciliation")
        < call_order.index("mature-catch-up")
    )

    managed_history_bootstrap.ensure_anchor.assert_called_once_with(
        node_id=node_id,
        instance_id=instance_id,
    )

    reconciliation.reconcile_between.assert_called_once()

    reconciliation_call = (
        reconciliation.reconcile_between.call_args
    )

    reconciliation_start = (
        reconciliation_call.kwargs["start"]
    )
    reconciliation_end = (
        reconciliation_call.kwargs["end"]
    )

    expected_open_history_start = (
        reconciliation_end.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        - timedelta(days=1)
    )

    assert (
        reconciliation_start
        == expected_open_history_start
    )

    # D-2 is mature history and must be owned exclusively
    # by catch_up_mature_days(), never by startup replay.
    mature_day = (
        reconciliation_end.date()
        - timedelta(days=2)
    )

    assert reconciliation_start.date() > mature_day

    daily_history.catch_up_mature_days.assert_called_once()

    catch_up_call = (
        daily_history.catch_up_mature_days.call_args
    )

    assert (
        catch_up_call.kwargs["node_id"]
        == node_id
    )
    assert (
        catch_up_call.kwargs["instance_id"]
        == instance_id
    )
    assert (
        catch_up_call.kwargs["through"].tzinfo
        is not None
    )
