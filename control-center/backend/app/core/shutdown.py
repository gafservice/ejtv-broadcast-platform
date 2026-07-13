"""Operaciones ejecutadas al detener la aplicación."""

import logging

logger = logging.getLogger(__name__)


async def application_shutdown() -> None:
    """Libera los recursos de la aplicación."""

    logger.info("Finalizando EJTV Control Center Backend.")
