"""Operaciones ejecutadas al iniciar la aplicación."""

import logging

from app.core.config import Settings
from app.core.version import APP_VERSION
from app.identity.bootstrap_admin import (
    build_bootstrap_service,
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

    bootstrap_service = build_bootstrap_service(
        settings
    )

    logger.info(
        "Persistencia de Identity inicializada.",
    )

    catalog_result = (
        bootstrap_service.synchronize_catalog()
    )

    logger.info(
        (
            "Catálogo de Identity sincronizado: "
            "creados=%d, actualizados=%d, "
            "sin_cambios=%d."
        ),
        len(catalog_result.created),
        len(catalog_result.updated),
        len(catalog_result.unchanged),
    )

    integrity_result = (
        bootstrap_service.verify_integrity()
    )

    if not integrity_result.valid:
        raise RuntimeError(
            "Identity catalog integrity verification failed: "
            f"missing={integrity_result.missing_roles}, "
            f"unexpected={integrity_result.unexpected_roles}, "
            f"mismatched={integrity_result.mismatched_roles}"
        )

    logger.info(
        "Integridad del catálogo de Identity verificada.",
    )
