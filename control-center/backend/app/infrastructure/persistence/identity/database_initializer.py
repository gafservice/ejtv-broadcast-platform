"""Inicialización de la persistencia del subsistema Identity."""

from sqlalchemy import Engine

from app.infrastructure.persistence.database import (
    Base,
    create_database_engine,
)

# Estos imports registran las tablas ORM en Base.metadata.
from app.infrastructure.persistence.audit.models import AuditLogModel
from app.infrastructure.persistence.identity.models import (
    PermissionModel,
    RoleModel,
    UserModel,
)


def initialize_identity_database(
    database_url: str,
    *,
    echo: bool = False,
) -> Engine:
    """Crea el motor y las tablas requeridas por Identity."""

    engine = create_database_engine(
        database_url,
        echo=echo,
    )

    Base.metadata.create_all(engine)

    return engine
