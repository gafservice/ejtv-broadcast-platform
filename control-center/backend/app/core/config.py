"""Configuración centralizada de la aplicación."""

from functools import lru_cache
from pathlib import Path
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
    """Parámetros configurables del Control Center."""

    app_name: str = "Control Center"

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

    mediamtx_api_url: str = "http://127.0.0.1:9997"

    mediamtx_api_timeout_seconds: float = Field(
        default=5.0,
        gt=0,
    )

    mediamtx_metrics_url: str = "http://127.0.0.1:9998"

    mediamtx_metrics_timeout_seconds: float = Field(
        default=5.0,
        gt=0,
    )

    geoip_database_path: str = (
        "data/geoip/GeoLite2-Country.mmdb"
    )

    # ------------------------------------------------------------------
    # NOC Node
    # ------------------------------------------------------------------

    node_network_policy_path: str = str(
        (
            Path(__file__).resolve().parents[2]
            / "config"
            / "nodes"
            / "ejtv-01.yaml"
        )
    )

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    identity_database_url: str = (
        "sqlite:///data/control-center.db"
    )

    jwt_secret_key: str = (
        "CHANGE_THIS_SECRET_KEY_WITH_AT_LEAST_32_BYTES"
    )

    jwt_issuer: str = "control-center"
    jwt_audience: str = "control-center-api"

    jwt_expiration_seconds: int = Field(
        default=900,
        gt=0,
    )

    bcrypt_rounds: int = Field(
        default=12,
        ge=4,
        le=31,
    )

    bootstrap_admin_username: str = "administrator"
    bootstrap_admin_email: str = "admin@example.com"
    bootstrap_admin_password: str | None = None

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
