"""Operaciones ejecutadas al iniciar la aplicación."""

import logging

from app.core.config import Settings
from app.core.version import APP_VERSION
from app.infrastructure.persistence.identity.database_initializer import (
    initialize_identity_database,
)

logger = logging.getLogger(__name__)


async def application_startup(settings: Settings) -> None:
    """Inicializa recursos de la aplicación."""

    logger.info(
        "Iniciando %s versión %s.",
        settings.app_name,
        APP_VERSION,
    )
    logger.info(
        "Entorno activo: %s.",
        settings.environment,
    )

    initialize_identity_database(
        settings.identity_database_url,
        echo=False,
    )

    logger.info(
        "Persistencia de Identity inicializada.",
    )
