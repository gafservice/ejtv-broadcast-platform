from datetime import datetime, timezone

from app.noc.current_state.repository import (
    NodeHealthDiagnosticRepository,
)
from app.noc.current_state.sqlite_node_health_diagnostic_repository import (
    SQLiteNodeHealthDiagnosticRepository,
)
from app.noc.domain.network_interface_health import (
    NetworkInterfaceHealth,
)
from app.noc.domain.node_health import (
    NodeHealth,
    NodeHealthState,
)
from app.noc.domain.node_health_diagnostic import (
    NodeHealthDiagnostic,
)
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.history.sqlite_database import (
    SQLiteHistoryDatabase,
)


def _node_id() -> NodeId:
    return NodeId(
        id="node-001",
        name="node-001",
        display_name="Node 001",
        created_at=datetime(
            2026,
            9,
            3,
            10,
            0,
            tzinfo=timezone.utc,
        ),
    )


def _diagnostic(
    *,
    minute: int,
    state: NodeHealthState,
) -> NodeHealthDiagnostic:
    captured_at = datetime(
        2026,
        9,
        3,
        12,
        minute,
        0,
        123456,
        tzinfo=timezone.utc,
    )

    return NodeHealthDiagnostic(
        captured_at=captured_at,
        health=NodeHealth(state),
        system_health=NodeHealth(
            NodeHealthState.HEALTHY
        ),
        network_health=NodeHealth(state),
        network_interfaces=(
            NetworkInterfaceHealth(
                interface="ens2f0",
                state=state,
                observed_at=captured_at,
                reason=f"state at minute {minute}",
                carrier_ok=True,
                traffic_ok=(
                    state is NodeHealthState.HEALTHY
                ),
                error_rate=0.001,
                drop_rate=0.002,
            ),
        ),
    )


def _repository(
    tmp_path,
) -> SQLiteNodeHealthDiagnosticRepository:
    database = SQLiteHistoryDatabase(
        tmp_path / "history.sqlite3"
    )

    return SQLiteNodeHealthDiagnosticRepository(
        database
    )


def test_repository_satisfies_current_state_protocol(
    tmp_path,
) -> None:
    repository = _repository(tmp_path)

    assert isinstance(
        repository,
        NodeHealthDiagnosticRepository,
    )


def test_latest_returns_none_when_state_does_not_exist(
    tmp_path,
) -> None:
    repository = _repository(tmp_path)

    result = repository.latest(
        node_id=_node_id(),
        instance_id=NodeInstanceId(
            "instance-001"
        ),
    )

    assert result is None


def test_save_and_latest_round_trip_complete_diagnostic(
    tmp_path,
) -> None:
    repository = _repository(tmp_path)

    node_id = _node_id()
    instance_id = NodeInstanceId(
        "instance-001"
    )
    diagnostic = _diagnostic(
        minute=5,
        state=NodeHealthState.WARNING,
    )

    repository.save(
        node_id=node_id,
        instance_id=instance_id,
        diagnostic=diagnostic,
    )

    result = repository.latest(
        node_id=node_id,
        instance_id=instance_id,
    )

    assert result == diagnostic


def test_newer_diagnostic_replaces_older_state(
    tmp_path,
) -> None:
    repository = _repository(tmp_path)

    node_id = _node_id()
    instance_id = NodeInstanceId(
        "instance-001"
    )

    older = _diagnostic(
        minute=1,
        state=NodeHealthState.WARNING,
    )
    newer = _diagnostic(
        minute=5,
        state=NodeHealthState.CRITICAL,
    )

    repository.save(
        node_id=node_id,
        instance_id=instance_id,
        diagnostic=older,
    )
    repository.save(
        node_id=node_id,
        instance_id=instance_id,
        diagnostic=newer,
    )

    assert repository.latest(
        node_id=node_id,
        instance_id=instance_id,
    ) == newer


def test_older_diagnostic_cannot_replace_newer_state(
    tmp_path,
) -> None:
    repository = _repository(tmp_path)

    node_id = _node_id()
    instance_id = NodeInstanceId(
        "instance-001"
    )

    newer = _diagnostic(
        minute=5,
        state=NodeHealthState.CRITICAL,
    )
    older = _diagnostic(
        minute=1,
        state=NodeHealthState.WARNING,
    )

    repository.save(
        node_id=node_id,
        instance_id=instance_id,
        diagnostic=newer,
    )
    repository.save(
        node_id=node_id,
        instance_id=instance_id,
        diagnostic=older,
    )

    assert repository.latest(
        node_id=node_id,
        instance_id=instance_id,
    ) == newer


def test_state_is_isolated_by_node_instance(
    tmp_path,
) -> None:
    repository = _repository(tmp_path)

    node_id = _node_id()

    first_instance = NodeInstanceId(
        "instance-001"
    )
    second_instance = NodeInstanceId(
        "instance-002"
    )

    first = _diagnostic(
        minute=1,
        state=NodeHealthState.HEALTHY,
    )
    second = _diagnostic(
        minute=2,
        state=NodeHealthState.DEGRADED,
    )

    repository.save(
        node_id=node_id,
        instance_id=first_instance,
        diagnostic=first,
    )
    repository.save(
        node_id=node_id,
        instance_id=second_instance,
        diagnostic=second,
    )

    assert repository.latest(
        node_id=node_id,
        instance_id=first_instance,
    ) == first

    assert repository.latest(
        node_id=node_id,
        instance_id=second_instance,
    ) == second


def test_state_is_shared_between_repository_instances(
    tmp_path,
) -> None:
    database_path = tmp_path / "history.sqlite3"

    writer = SQLiteNodeHealthDiagnosticRepository(
        SQLiteHistoryDatabase(database_path)
    )
    reader = SQLiteNodeHealthDiagnosticRepository(
        SQLiteHistoryDatabase(database_path)
    )

    node_id = _node_id()
    instance_id = NodeInstanceId(
        "instance-001"
    )
    diagnostic = _diagnostic(
        minute=5,
        state=NodeHealthState.DEGRADED,
    )

    writer.save(
        node_id=node_id,
        instance_id=instance_id,
        diagnostic=diagnostic,
    )

    result = reader.latest(
        node_id=node_id,
        instance_id=instance_id,
    )

    assert result == diagnostic
