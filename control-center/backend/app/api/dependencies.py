"""Construcción de dependencias utilizadas por la API."""

from functools import lru_cache

from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.adapters.linux.linux_system_adapter import LinuxSystemAdapter
from app.core.config import get_settings
from app.dashboard.application import DashboardApplication
from app.dashboard.live_monitor import build_dashboard_application
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
from app.noc.registry.registry import NodeRegistry
from app.noc.services.alarm_service import AlarmService
from app.noc.services.heartbeat_service import HeartbeatService
from app.noc.services.metric_service import MetricService
from app.noc.services.snapshot_service import SnapshotService
from app.noc.runtime.telemetry_refresh import (
    TelemetryRefreshService,
)
from app.services.authentication_service import AuthenticationService
from app.services.identity_administration_service import (
    IdentityAdministrationService,
)
from app.services.authorization_service import AuthorizationService
from app.services.system_service import SystemService


@lru_cache
def get_system_service() -> SystemService:
    """Construye el servicio de sistema para el entorno actual."""

    adapter = LinuxSystemAdapter()
    return SystemService(adapter)


@lru_cache
def get_dashboard_application() -> DashboardApplication:
    """Construye la aplicación coordinadora del dashboard."""

    return build_dashboard_application()


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
def get_metric_service() -> MetricService:
    """Construye el servicio compartido de métricas."""

    return MetricService(
        get_node_registry()
    )


@lru_cache
def get_alarm_service() -> AlarmService:
    """Construye el servicio compartido de alarmas."""

    return AlarmService(
        get_node_registry()
    )


@lru_cache
def get_snapshot_service() -> SnapshotService:
    """Construye el servicio compartido de Snapshots."""

    return SnapshotService(
        get_node_registry()
    )


@lru_cache
def get_telemetry_refresh_service() -> TelemetryRefreshService:
    """Construye el refresco periódico compartido de telemetría NOC."""

    return TelemetryRefreshService(
        system_service=get_system_service(),
        metric_service=get_metric_service(),
    )
