"""Configuración centralizada de la aplicación."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.constants import (
    DEFAULT_HOST,
    DEFAULT_LOG_LEVEL,
    DEFAULT_PORT,
    ENVIRONMENT_DEVELOPMENT,
)


class Settings(BaseSettings):
    """Parámetros configurables del EJTV Control Center."""

    app_name: str = "EJTV Control Center"

    environment: Literal[
        "development",
        "testing",
        "production",
    ] = ENVIRONMENT_DEVELOPMENT

    debug: bool = True

    host: str = DEFAULT_HOST
    port: int = Field(default=DEFAULT_PORT, ge=1, le=65535)

    log_level: str = DEFAULT_LOG_LEVEL
    log_directory: str = "../logs"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Retorna una única instancia de configuración."""

    return Settings()
