"""Tests for NOC runtime dependency composition."""

from app.api.dependencies import (
    get_alarm_history_repository,
    get_alarm_recovery_service,
    get_alarm_service,
    get_event_service,
    get_event_history_repository,
    get_history_query_service,
    get_historical_range_repository,
    get_managed_history_repository,
    get_managed_history_bootstrap_service,
    get_daily_history_maintenance_runtime,
    get_noc_history_database,
    get_node_health_diagnostic_repository,
    get_health_service,
    get_capacity_service,
    get_heartbeat_service,
    get_metric_service,
    get_noc_repository,
    get_node_registry,
    get_snapshot_service,
    get_mediamtx_http_client,
    get_mediamtx_adapter,
    get_geoip_service,
    get_mediamtx_session_adapter,
    get_node_session_policy_config,
    get_session_transition_event_service,
    get_session_alarm_runtime,
    get_session_operational_runtime,
    get_streaming_service,
    get_session_observation_runtime,
    get_telemetry_refresh_service,
    get_telemetry_observation_runtime,
)
from app.noc.infrastructure.memory_repository import (
    InMemoryNodeRepository,
)
from app.noc.history.sqlite_historical_range_repository import (
    SQLiteHistoricalRangeRepository,
)
from app.noc.history.sqlite_managed_history_repository import (
    SQLiteManagedHistoryRepository,
)
from app.noc.runtime.daily_history_maintenance import (
    DailyHistoryMaintenanceRuntime,
)
from app.noc.current_state.sqlite_node_health_diagnostic_repository import (
    SQLiteNodeHealthDiagnosticRepository,
)
from app.noc.registry.registry import NodeRegistry
from app.noc.runtime.session_alarm_runtime import (
    SessionAlarmRuntime,
)
from app.noc.runtime.session_observation_runtime import (
    SessionObservationRuntime,
)
from app.noc.runtime.session_operational_runtime import (
    SessionOperationalRuntime,
)
from app.noc.runtime.telemetry_observation_runtime import (
    TelemetryObservationRuntime,
)
from app.noc.services.alarm_service import AlarmService
from app.noc.services.capacity_service import CapacityService
from app.noc.services.health_service import HealthService
from app.noc.services.heartbeat_service import HeartbeatService
from app.noc.services.history_query_service import (
    HistoryQueryService,
)
from app.noc.services.managed_history_bootstrap_service import (
    ManagedHistoryBootstrapService,
)
from app.noc.services.metric_service import MetricService
from app.noc.services.snapshot_service import SnapshotService


def clear_noc_dependency_caches() -> None:
    """Reset all NOC dependency factories."""

    get_session_observation_runtime.cache_clear()
    get_telemetry_observation_runtime.cache_clear()
    get_telemetry_refresh_service.cache_clear()
    get_node_health_diagnostic_repository.cache_clear()
    get_streaming_service.cache_clear()
    get_session_operational_runtime.cache_clear()
    get_session_alarm_runtime.cache_clear()
    get_session_transition_event_service.cache_clear()
    get_node_session_policy_config.cache_clear()
    get_mediamtx_session_adapter.cache_clear()
    get_geoip_service.cache_clear()
    get_mediamtx_adapter.cache_clear()
    get_mediamtx_http_client.cache_clear()
    get_event_service.cache_clear()
    get_snapshot_service.cache_clear()
    get_alarm_recovery_service.cache_clear()
    get_daily_history_maintenance_runtime.cache_clear()
    get_managed_history_bootstrap_service.cache_clear()
    get_managed_history_repository.cache_clear()
    get_historical_range_repository.cache_clear()
    get_history_query_service.cache_clear()
    get_alarm_service.cache_clear()
    get_alarm_history_repository.cache_clear()
    get_event_history_repository.cache_clear()
    get_noc_history_database.cache_clear()
    get_metric_service.cache_clear()
    get_heartbeat_service.cache_clear()
    get_health_service.cache_clear()
    get_capacity_service.cache_clear()
    get_node_registry.cache_clear()
    get_noc_repository.cache_clear()


def setup_function() -> None:
    clear_noc_dependency_caches()


def teardown_function() -> None:
    clear_noc_dependency_caches()


def test_noc_repository_is_cached() -> None:
    first = get_noc_repository()
    second = get_noc_repository()

    assert first is second

    assert isinstance(
        first,
        InMemoryNodeRepository,
    )


def test_node_registry_is_cached() -> None:
    first = get_node_registry()
    second = get_node_registry()

    assert first is second

    assert isinstance(
        first,
        NodeRegistry,
    )


def test_registry_uses_shared_repository() -> None:
    repository = get_noc_repository()
    registry = get_node_registry()

    assert registry.repository is repository


def test_heartbeat_service_is_cached() -> None:
    first = get_heartbeat_service()
    second = get_heartbeat_service()

    assert first is second

    assert isinstance(
        first,
        HeartbeatService,
    )


def test_metric_service_is_cached() -> None:
    first = get_metric_service()
    second = get_metric_service()

    assert first is second

    assert isinstance(
        first,
        MetricService,
    )


def test_alarm_service_is_cached() -> None:
    first = get_alarm_service()
    second = get_alarm_service()

    assert first is second

    assert isinstance(
        first,
        AlarmService,
    )


def test_snapshot_service_is_cached() -> None:
    first = get_snapshot_service()
    second = get_snapshot_service()

    assert first is second

    assert isinstance(
        first,
        SnapshotService,
    )


def test_heartbeat_service_uses_shared_registry() -> None:
    registry = get_node_registry()

    assert (
        get_heartbeat_service().registry
        is registry
    )


def test_metric_service_uses_shared_registry() -> None:
    registry = get_node_registry()

    assert (
        get_metric_service().registry
        is registry
    )


def test_snapshot_service_uses_shared_registry() -> None:
    registry = get_node_registry()

    assert (
        get_snapshot_service().registry
        is registry
    )


def test_alarm_service_uses_shared_registry() -> None:
    registry = get_node_registry()

    assert (
        get_alarm_service()._registry
        is registry
    )


def test_all_services_share_same_registry() -> None:
    registry = get_node_registry()

    assert get_heartbeat_service().registry is registry
    assert get_metric_service().registry is registry
    assert get_alarm_service()._registry is registry
    assert get_snapshot_service().registry is registry


def test_repository_state_is_visible_through_registry() -> None:
    from app.noc.domain.node import Node
    from app.noc.domain.node_id import NodeId
    from app.noc.domain.node_type import NodeType

    repository = get_noc_repository()
    registry = get_node_registry()

    node = Node(
        node_id=NodeId.create(
            id="streaming-core",
            name="streaming",
            display_name="Streaming Core",
        ),
        node_type=NodeType.STREAMING,
    )

    registry.register(node)

    assert repository.count() == 1

    assert repository.get(
        node.node_id
    ) is node


def test_registry_state_is_visible_to_services() -> None:
    from app.noc.domain.node import Node
    from app.noc.domain.node_id import NodeId
    from app.noc.domain.node_type import NodeType

    registry = get_node_registry()

    node = Node(
        node_id=NodeId.create(
            id="streaming-core",
            name="streaming",
            display_name="Streaming Core",
        ),
        node_type=NodeType.STREAMING,
    )

    instance = node.create_instance(
        instance_id="streaming-primary"
    )

    registry.register(node)

    assert (
        get_heartbeat_service().is_present(
            node.node_id,
            instance.instance_id,
        )
        is False
    )

    assert (
        get_metric_service().current(
            node.node_id,
            instance.instance_id,
        ).samples
        == ()
    )

    assert (
        get_alarm_service().list_all(
            node.node_id,
            instance.instance_id,
        )
        == ()
    )


def test_capacity_service_is_cached() -> None:
    first = get_capacity_service()
    second = get_capacity_service()

    assert first is second

    assert isinstance(
        first,
        CapacityService,
    )


def test_capacity_service_uses_shared_registry() -> None:
    registry = get_node_registry()

    assert (
        get_capacity_service().registry
        is registry
    )


def test_health_service_is_cached() -> None:
    first = get_health_service()
    second = get_health_service()

    assert first is second

    assert isinstance(
        first,
        HealthService,
    )


def test_health_service_uses_shared_registry() -> None:
    registry = get_node_registry()

    assert (
        get_health_service().registry
        is registry
    )


def test_noc_history_database_is_cached() -> None:
    first = get_noc_history_database()
    second = get_noc_history_database()

    assert first is second


def test_history_repositories_share_database() -> None:
    database = get_noc_history_database()

    event_history = get_event_history_repository()
    alarm_history = get_alarm_history_repository()

    assert event_history._database is database
    assert alarm_history._database is database


def test_alarm_service_uses_shared_history_repository() -> None:
    history = get_alarm_history_repository()

    assert (
        get_alarm_service().history_repository
        is history
    )


def test_alarm_recovery_service_is_cached() -> None:
    first = get_alarm_recovery_service()
    second = get_alarm_recovery_service()

    assert first is second


def test_alarm_recovery_service_uses_shared_dependencies() -> None:
    service = get_alarm_recovery_service()

    assert service._registry is get_node_registry()
    assert (
        service._history_repository
        is get_alarm_history_repository()
    )


def test_history_query_service_is_cached() -> None:
    first = get_history_query_service()
    second = get_history_query_service()

    assert first is second
    assert isinstance(
        first,
        HistoryQueryService,
    )


def test_history_query_service_uses_shared_history_repositories() -> None:
    service = get_history_query_service()

    assert (
        service.event_repository
        is get_event_history_repository()
    )

    assert (
        service.alarm_repository
        is get_alarm_history_repository()
    )


def test_event_service_is_cached() -> None:
    first = get_event_service()
    second = get_event_service()

    assert first is second


def test_event_service_uses_shared_noc_dependencies() -> None:
    service = get_event_service()

    assert service.registry is get_node_registry()
    assert (
        service.history_repository
        is get_event_history_repository()
    )
    assert (
        service.evidence_writer
        is get_alarm_service().evidence_writer
    )


def test_mediamtx_runtime_dependencies_are_cached() -> None:
    assert (
        get_mediamtx_http_client()
        is get_mediamtx_http_client()
    )
    assert (
        get_mediamtx_adapter()
        is get_mediamtx_adapter()
    )
    assert (
        get_geoip_service()
        is get_geoip_service()
    )
    assert (
        get_mediamtx_session_adapter()
        is get_mediamtx_session_adapter()
    )
    assert (
        get_streaming_service()
        is get_streaming_service()
    )


def test_session_transition_service_uses_shared_event_service() -> None:
    service = get_session_transition_event_service()

    assert service.event_service is get_event_service()


def test_session_alarm_runtime_is_cached() -> None:
    first = get_session_alarm_runtime()
    second = get_session_alarm_runtime()

    assert first is second
    assert isinstance(first, SessionAlarmRuntime)


def test_session_operational_runtime_uses_shared_components() -> None:
    runtime = get_session_operational_runtime()

    assert isinstance(
        runtime,
        SessionOperationalRuntime,
    )
    assert (
        runtime._transition_event_service
        is get_session_transition_event_service()
    )
    assert (
        runtime._alarm_runtime
        is get_session_alarm_runtime()
    )


def test_session_observation_runtime_uses_shared_components() -> None:
    runtime = get_session_observation_runtime()

    assert isinstance(
        runtime,
        SessionObservationRuntime,
    )
    assert (
        runtime._mediamtx_adapter
        is get_mediamtx_adapter()
    )
    assert (
        runtime._session_adapter
        is get_mediamtx_session_adapter()
    )
    assert (
        runtime._streaming_service
        is get_streaming_service()
    )
    assert (
        runtime._operational_runtime
        is get_session_operational_runtime()
    )

def test_node_health_diagnostic_repository_is_cached() -> None:
    first = get_node_health_diagnostic_repository()
    second = get_node_health_diagnostic_repository()

    assert first is second

    assert isinstance(
        first,
        SQLiteNodeHealthDiagnosticRepository,
    )

    assert (
        first._database
        is get_noc_history_database()
    )


def test_telemetry_observation_runtime_uses_shared_components() -> None:
    runtime = get_telemetry_observation_runtime()

    assert isinstance(
        runtime,
        TelemetryObservationRuntime,
    )

    assert (
        runtime.telemetry_refresh_service
        is get_telemetry_refresh_service()
    )

    assert (
        runtime.health_diagnostic_repository
        is get_node_health_diagnostic_repository()
    )



def test_historical_range_repository_is_cached_and_uses_shared_database(
) -> None:
    database = get_noc_history_database()

    first = get_historical_range_repository()
    second = get_historical_range_repository()

    assert first is second
    assert isinstance(
        first,
        SQLiteHistoricalRangeRepository,
    )
    assert first._database is database


def test_daily_history_maintenance_runtime_is_cached_and_uses_managed_history(
) -> None:
    first = get_daily_history_maintenance_runtime()
    second = get_daily_history_maintenance_runtime()

    assert first is second
    assert isinstance(
        first,
        DailyHistoryMaintenanceRuntime,
    )
    assert (
        first._managed_history_repository
        is get_managed_history_repository()
    )


def test_managed_history_repository_is_cached_and_uses_shared_database(
) -> None:
    database = get_noc_history_database()

    first = get_managed_history_repository()
    second = get_managed_history_repository()

    assert first is second
    assert isinstance(
        first,
        SQLiteManagedHistoryRepository,
    )
    assert first._database is database


def test_managed_history_bootstrap_service_is_cached_and_uses_shared_components(
) -> None:
    first = get_managed_history_bootstrap_service()
    second = get_managed_history_bootstrap_service()

    assert first is second
    assert isinstance(
        first,
        ManagedHistoryBootstrapService,
    )

    assert (
        first._managed_history_repository
        is get_managed_history_repository()
    )

    assert (
        first._historical_range_repository
        is get_historical_range_repository()
    )


def test_managed_history_dependencies_share_history_database() -> None:
    database = get_noc_history_database()

    managed = get_managed_history_repository()
    historical = get_historical_range_repository()

    assert managed._database is database
    assert historical._database is database
