"""Construcción de dependencias utilizadas por la API."""

from functools import lru_cache

from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.adapters.linux.linux_system_adapter import LinuxSystemAdapter
from app.adapters.mediamtx.adapter import MediaMTXAdapter
from app.adapters.mediamtx.client import MediaMTXClient
from app.adapters.mediamtx.session_adapter import MediaMTXSessionAdapter
from app.adapters.mediamtx.session_client import MediaMTXSessionClient
from app.core.http import HttpClient
from app.core.config import get_settings
from app.infrastructure.persistence.audit.sqlalchemy_audit_repository import (
    SQLAlchemyAuditRepository,
)
from app.infrastructure.persistence.database import (
    create_database_engine,
    create_session_factory,
)
from app.infrastructure.persistence.identity.sqlalchemy_user_repository import (
    SQLAlchemyUserRepository,
)
from app.infrastructure.security.bcrypt_password_hasher import (
    BcryptPasswordHasher,
)
from app.infrastructure.security.jwt_token_provider import JWTTokenProvider
from app.noc.infrastructure.memory_repository import (
    InMemoryNodeRepository,
)
from app.noc.history.sqlite_alarm_repository import (
    SQLiteAlarmHistoryRepository,
)
from app.noc.history.sqlite_database import (
    SQLiteHistoryDatabase,
)
from app.noc.history.sqlite_event_repository import (
    SQLiteEventHistoryRepository,
)
from app.noc.history.filesystem_csv_export_repository import (
    FilesystemCsvExportRepository,
)
from app.noc.history.filesystem_pdf_export_repository import (
    FilesystemPdfExportRepository,
)
from app.noc.history.sqlite_historical_range_repository import (
    SQLiteHistoricalRangeRepository,
)
from app.noc.history.sqlite_managed_history_repository import (
    SQLiteManagedHistoryRepository,
)
from app.noc.current_state.sqlite_node_health_diagnostic_repository import (
    SQLiteNodeHealthDiagnosticRepository,
)
from app.noc.history.evidence_day_sealer import (
    EvidenceDaySealer,
)
from app.noc.history.jsonl_evidence_writer import (
    JsonlEvidenceWriter,
)
from app.noc.domain.node_network_policy_config import (
    NodeNetworkPolicyConfig,
)
from app.noc.domain.node_session_policy_config import (
    NodeSessionPolicyConfig,
)
from app.noc.infrastructure.node_network_policy_loader import (
    NodeNetworkPolicyLoader,
)
from app.noc.infrastructure.node_session_policy_loader import (
    NodeSessionPolicyLoader,
)
from app.noc.runtime.session_alarm_runtime import (
    SessionAlarmRuntime,
)
from app.noc.runtime.session_observation_runtime import (
    SessionObservationRuntime,
)
from app.noc.runtime.session_operational_runtime import (
    SessionOperationalRuntime,
)
from app.noc.registry.registry import NodeRegistry
from app.noc.services.alarm_service import AlarmService
from app.noc.services.critical_path_no_readers_alarm_service import (
    CriticalPathNoReadersAlarmService,
)
from app.noc.services.critical_path_unavailable_alarm_service import (
    CriticalPathUnavailableAlarmService,
)
from app.noc.services.critical_path_traffic_stalled_alarm_service import (
    CriticalPathTrafficStalledAlarmService,
)
from app.noc.services.event_service import EventService
from app.noc.services.expected_session_alarm_service import (
    ExpectedSessionAlarmService,
)
from app.noc.services.reconnect_flapping_alarm_service import (
    ReconnectFlappingAlarmService,
)
from app.noc.services.reconnect_flapping_evaluator import (
    ReconnectFlappingEvaluator,
)
from app.noc.services.session_transition_event_service import (
    SessionTransitionEventService,
)
from app.noc.services.alarm_recovery_service import (
    AlarmRecoveryService,
)
from app.noc.services.daily_alarm_continuity_service import (
    DailyAlarmContinuityService,
)
from app.noc.runtime.daily_history_maintenance import (
    DailyHistoryMaintenanceRuntime,
)
from app.noc.services.health_service import HealthService
from app.noc.services.history_query_service import (
    HistoryQueryService,
)
from app.noc.services.history_csv_export_service import (
    HistoryCsvExportService,
)
from app.noc.services.history_pdf_export_service import (
    HistoryPdfExportService,
)
from app.noc.services.evidence_reconciliation_service import (
    EvidenceReconciliationService,
)
from app.noc.services.managed_history_bootstrap_service import (
    ManagedHistoryBootstrapService,
)
from app.noc.services.heartbeat_service import HeartbeatService
from app.noc.services.capacity_service import CapacityService
from app.noc.services.metric_service import MetricService
from app.noc.services.snapshot_service import SnapshotService
from app.noc.runtime.telemetry_refresh import (
    TelemetryRefreshService,
)
from app.noc.runtime.telemetry_observation_runtime import (
    TelemetryObservationRuntime,
)
from app.noc.runtime.runtime_owner_lock import (
    RuntimeOwnerLock,
)
from app.services.authentication_service import AuthenticationService
from app.services.identity_administration_service import (
    IdentityAdministrationService,
)
from app.services.authorization_service import AuthorizationService
from app.services.geoip_service import GeoIPService
from app.services.streaming_service import StreamingService
from app.services.system_service import SystemService


@lru_cache
def get_system_service() -> SystemService:
    """Construye el servicio de sistema para el entorno actual."""

    adapter = LinuxSystemAdapter()
    return SystemService(adapter)


@lru_cache
def get_identity_database_engine() -> Engine:
    """Construye el motor de persistencia de Identity."""

    settings = get_settings()

    return create_database_engine(
        settings.identity_database_url,
        echo=False,
    )


@lru_cache
def get_identity_session_factory() -> sessionmaker[Session]:
    """Construye la fábrica de sesiones de Identity."""

    return create_session_factory(
        get_identity_database_engine()
    )


@lru_cache
def get_token_provider() -> JWTTokenProvider:
    """Construye el proveedor JWT compartido por la API."""

    settings = get_settings()

    return JWTTokenProvider(
        secret_key=settings.jwt_secret_key,
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
        expiration_seconds=settings.jwt_expiration_seconds,
    )


@lru_cache
def get_audit_repository() -> SQLAlchemyAuditRepository:
    """Construye el repositorio de auditoría de Identity."""

    return SQLAlchemyAuditRepository(
        get_identity_session_factory()
    )


@lru_cache
def get_authorization_service() -> AuthorizationService:
    """Construye el servicio de autorización."""

    return AuthorizationService(
        audit_repository=get_audit_repository()
    )


@lru_cache
def get_identity_administration_service(
) -> IdentityAdministrationService:
    """Construye el servicio administrativo de Identity."""

    settings = get_settings()

    return IdentityAdministrationService(
        user_repository=SQLAlchemyUserRepository(
            get_identity_session_factory()
        ),
        password_hasher=BcryptPasswordHasher(
            rounds=settings.bcrypt_rounds
        ),
        audit_repository=get_audit_repository(),
    )


@lru_cache
def get_authentication_service() -> AuthenticationService:
    """Construye el servicio de autenticación."""

    settings = get_settings()
    session_factory = get_identity_session_factory()

    user_repository = SQLAlchemyUserRepository(
        session_factory
    )

    password_hasher = BcryptPasswordHasher(
        rounds=settings.bcrypt_rounds
    )

    return AuthenticationService(
        user_repository=user_repository,
        password_hasher=password_hasher,
        token_provider=get_token_provider(),
        audit_repository=get_audit_repository(),
    )


@lru_cache
def get_runtime_owner_lock() -> RuntimeOwnerLock:
    """Construye el lock interproceso del Runtime Owner NOC."""

    settings = get_settings()

    return RuntimeOwnerLock(
        settings.noc_runtime_lock_path
    )


@lru_cache
def get_noc_history_database() -> SQLiteHistoryDatabase:
    """Construye la base durable compartida del histórico NOC."""

    settings = get_settings()

    return SQLiteHistoryDatabase(
        settings.noc_history_database_path
    )


@lru_cache
def get_noc_evidence_writer() -> JsonlEvidenceWriter:
    """Construye el writer compartido de evidencia NOC."""

    settings = get_settings()

    return JsonlEvidenceWriter(
        settings.noc_evidence_path
    )


@lru_cache
def get_event_history_repository() -> SQLiteEventHistoryRepository:
    """Construye el repositorio durable de eventos NOC."""

    return SQLiteEventHistoryRepository(
        get_noc_history_database()
    )


@lru_cache
def get_alarm_history_repository() -> SQLiteAlarmHistoryRepository:
    """Construye el repositorio durable de alarmas NOC."""

    return SQLiteAlarmHistoryRepository(
        get_noc_history_database()
    )


@lru_cache
def get_historical_range_repository(
) -> SQLiteHistoricalRangeRepository:
    """Construye el descubridor del rango histórico durable NOC."""

    return SQLiteHistoricalRangeRepository(
        get_noc_history_database()
    )



@lru_cache
def get_managed_history_repository(
) -> SQLiteManagedHistoryRepository:
    """Construye la autoridad durable del inicio histórico administrado."""

    return SQLiteManagedHistoryRepository(
        get_noc_history_database()
    )


@lru_cache
def get_managed_history_bootstrap_service(
) -> ManagedHistoryBootstrapService:
    """Construye el bootstrap durable del histórico administrado."""

    return ManagedHistoryBootstrapService(
        managed_history_repository=(
            get_managed_history_repository()
        ),
        historical_range_repository=(
            get_historical_range_repository()
        ),
    )


@lru_cache
def get_node_health_diagnostic_repository(
) -> SQLiteNodeHealthDiagnosticRepository:
    """Construye el repositorio compartido de diagnóstico de salud."""

    return SQLiteNodeHealthDiagnosticRepository(
        get_noc_history_database()
    )


@lru_cache
def get_noc_repository() -> InMemoryNodeRepository:
    """Construye el repositorio compartido del runtime NOC."""

    return InMemoryNodeRepository()


@lru_cache
def get_node_registry() -> NodeRegistry:
    """Construye el registro lógico compartido de Nodes."""

    return NodeRegistry(
        get_noc_repository()
    )


@lru_cache
def get_heartbeat_service() -> HeartbeatService:
    """Construye el servicio compartido de Heartbeats."""

    return HeartbeatService(
        get_node_registry()
    )


@lru_cache
def get_capacity_service() -> CapacityService:
    """Construye el servicio compartido de capacidad."""

    return CapacityService(
        get_node_registry()
    )


@lru_cache
def get_health_service() -> HealthService:
    """Construye el servicio compartido de salud del Node."""

    return HealthService(
        get_node_registry()
    )


@lru_cache
def get_metric_service() -> MetricService:
    """Construye el servicio compartido de métricas."""

    return MetricService(
        get_node_registry()
    )


@lru_cache
def get_event_service() -> EventService:
    """Construye el servicio compartido de eventos."""

    return EventService(
        get_node_registry(),
        history_repository=get_event_history_repository(),
        evidence_writer=get_noc_evidence_writer(),
    )


@lru_cache
def get_alarm_service() -> AlarmService:
    """Construye el servicio compartido de alarmas."""

    return AlarmService(
        get_node_registry(),
        history_repository=get_alarm_history_repository(),
        evidence_writer=get_noc_evidence_writer(),
    )


@lru_cache
def get_history_query_service() -> HistoryQueryService:
    """Construye el servicio compartido de consulta histórica NOC."""

    return HistoryQueryService(
        event_repository=get_event_history_repository(),
        alarm_repository=get_alarm_history_repository(),
    )


@lru_cache
def get_csv_export_repository() -> FilesystemCsvExportRepository:
    """Construye el publicador filesystem de exportaciones CSV NOC."""

    return FilesystemCsvExportRepository()


@lru_cache
def get_history_csv_export_service() -> HistoryCsvExportService:
    """Construye el servicio compartido de exportación CSV histórica."""

    return HistoryCsvExportService(
        event_repository=get_event_history_repository(),
        alarm_repository=get_alarm_history_repository(),
        export_repository=get_csv_export_repository(),
    )


@lru_cache
def get_pdf_export_repository() -> FilesystemPdfExportRepository:
    """Construye el publicador filesystem de exportaciones PDF NOC."""

    return FilesystemPdfExportRepository()


@lru_cache
def get_history_pdf_export_service() -> HistoryPdfExportService:
    """Construye el servicio compartido de exportación PDF histórica."""

    return HistoryPdfExportService(
        event_repository=get_event_history_repository(),
        alarm_repository=get_alarm_history_repository(),
        export_repository=get_pdf_export_repository(),
    )


@lru_cache
def get_evidence_reconciliation_service(
) -> EvidenceReconciliationService:
    """Construye la reconciliación SQLite -> JSONL."""

    return EvidenceReconciliationService(
        event_repository=get_event_history_repository(),
        alarm_repository=get_alarm_history_repository(),
        evidence_writer=get_noc_evidence_writer(),
    )


@lru_cache
def get_daily_alarm_continuity_service(
) -> DailyAlarmContinuityService:
    """Construye la continuidad diaria durable de alarmas NOC."""

    return DailyAlarmContinuityService(
        get_alarm_history_repository(),
    )


@lru_cache
def get_evidence_day_sealer() -> EvidenceDaySealer:
    """Construye el sellador diario SHA-256 del NOC."""

    return EvidenceDaySealer(
        get_noc_evidence_writer().root_path
    )


@lru_cache
def get_daily_history_maintenance_runtime(
) -> DailyHistoryMaintenanceRuntime:
    """Construye el mantenimiento histórico diario del NOC."""

    return DailyHistoryMaintenanceRuntime(
        continuity_service=(
            get_daily_alarm_continuity_service()
        ),
        reconciliation_service=(
            get_evidence_reconciliation_service()
        ),
        evidence_day_sealer=(
            get_evidence_day_sealer()
        ),
        managed_history_repository=(
            get_managed_history_repository()
        ),
    )


@lru_cache
def get_alarm_recovery_service() -> AlarmRecoveryService:
    """Construye la recuperación durable de alarmas NOC."""

    return AlarmRecoveryService(
        registry=get_node_registry(),
        history_repository=get_alarm_history_repository(),
    )


@lru_cache
def get_snapshot_service() -> SnapshotService:
    """Construye el servicio compartido de Snapshots."""

    return SnapshotService(
        get_node_registry()
    )


@lru_cache
def get_node_network_policy_config() -> NodeNetworkPolicyConfig:
    """Carga la política declarativa de red del Node actual."""

    settings = get_settings()

    return NodeNetworkPolicyLoader().load(
        settings.node_network_policy_path
    )


@lru_cache
def get_telemetry_refresh_service() -> TelemetryRefreshService:
    """Construye el refresco periódico compartido de telemetría NOC."""

    network_policy = (
        get_node_network_policy_config()
    )

    return TelemetryRefreshService(
        system_service=get_system_service(),
        metric_service=get_metric_service(),
        health_service=get_health_service(),
        network_policies=network_policy.interfaces,
    )

@lru_cache
def get_telemetry_observation_runtime(
) -> TelemetryObservationRuntime:
    """Construye el coordinador propietario de telemetría NOC."""

    return TelemetryObservationRuntime(
        telemetry_refresh_service=(
            get_telemetry_refresh_service()
        ),
        health_diagnostic_repository=(
            get_node_health_diagnostic_repository()
        ),
    )


@lru_cache
def get_mediamtx_http_client() -> HttpClient:
    """Construye el cliente HTTP compartido de MediaMTX."""

    settings = get_settings()

    return HttpClient(
        base_url=settings.mediamtx_api_url,
        timeout=settings.mediamtx_api_timeout_seconds,
    )


@lru_cache
def get_mediamtx_adapter() -> MediaMTXAdapter:
    """Construye el adaptador compartido de paths MediaMTX."""

    return MediaMTXAdapter(
        MediaMTXClient(
            get_mediamtx_http_client()
        )
    )


@lru_cache
def get_geoip_service() -> GeoIPService:
    """Construye el servicio GeoIP compartido."""

    settings = get_settings()

    return GeoIPService(
        settings.geoip_database_path
    )


@lru_cache
def get_mediamtx_session_adapter() -> MediaMTXSessionAdapter:
    """Construye el adaptador compartido de sesiones MediaMTX."""

    return MediaMTXSessionAdapter(
        MediaMTXSessionClient(
            get_mediamtx_http_client()
        ),
        get_geoip_service(),
    )


@lru_cache
def get_node_session_policy_config() -> NodeSessionPolicyConfig:
    """Carga la política declarativa de sesiones del Node actual."""

    settings = get_settings()

    return NodeSessionPolicyLoader().load(
        settings.node_network_policy_path
    )


@lru_cache
def get_session_transition_event_service(
) -> SessionTransitionEventService:
    """Construye el servicio de eventos de transición de sesiones."""

    return SessionTransitionEventService(
        event_service=get_event_service()
    )


@lru_cache
def get_session_alarm_runtime() -> SessionAlarmRuntime:
    """Construye las políticas operacionales de alarmas de sesión."""

    session_policy = get_node_session_policy_config()

    reconnect_flapping_evaluator = (
        ReconnectFlappingEvaluator(
            policy=session_policy.reconnect_flapping
        )
        if session_policy.reconnect_flapping is not None
        else ReconnectFlappingEvaluator()
    )

    return SessionAlarmRuntime(
        expected_session_alarm_service=(
            ExpectedSessionAlarmService(
                alarm_service=get_alarm_service()
            )
        ),
        reconnect_flapping_alarm_service=(
            ReconnectFlappingAlarmService(
                alarm_service=get_alarm_service()
            )
        ),
        critical_path_alarm_service=(
            CriticalPathNoReadersAlarmService(
                alarm_service=get_alarm_service()
            )
        ),
        critical_path_unavailable_alarm_service=(
            CriticalPathUnavailableAlarmService(
                alarm_service=get_alarm_service()
            )
        ),
        critical_path_traffic_stalled_alarm_service=(
            CriticalPathTrafficStalledAlarmService(
                alarm_service=get_alarm_service()
            )
        ),
        expected_session_policies=(
            session_policy.expected_sessions
        ),
        critical_path_policies=(
            session_policy.critical_paths
        ),
        reconnect_flapping_evaluator=(
            reconnect_flapping_evaluator
        ),
        reconnect_flapping_enabled=(
            session_policy.has_reconnect_flapping
        ),
    )


@lru_cache
def get_session_operational_runtime() -> SessionOperationalRuntime:
    """Construye el coordinador operacional de sesiones."""

    return SessionOperationalRuntime(
        transition_event_service=(
            get_session_transition_event_service()
        ),
        alarm_runtime=get_session_alarm_runtime(),
    )


@lru_cache
def get_streaming_service() -> StreamingService:
    """Construye el servicio compartido de medición multimedia."""

    return StreamingService()


@lru_cache
def get_session_observation_runtime() -> SessionObservationRuntime:
    """Construye el observador periódico propiedad del Runtime Owner."""

    return SessionObservationRuntime(
        mediamtx_adapter=get_mediamtx_adapter(),
        session_adapter=get_mediamtx_session_adapter(),
        streaming_service=get_streaming_service(),
        operational_runtime=get_session_operational_runtime(),
    )
