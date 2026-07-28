"""Servicio para resolver país y proveedor de una dirección IP."""

from __future__ import annotations

from dataclasses import dataclass
from ipaddress import ip_address
import logging
from pathlib import Path

import geoip2.database
from geoip2.errors import AddressNotFoundError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GeoIPResult:
    """Resultado de una resolución GeoIP."""

    country_code: str | None = None
    country_name: str | None = None
    asn: int | None = None
    asn_organization: str | None = None


class GeoIPService:
    """Resuelve país y proveedor de red utilizando MaxMind."""

    def __init__(
        self,
        country_database_path: str,
        asn_database_path: str | None = None,
    ) -> None:
        self._country_database_path = Path(country_database_path)

        self._asn_database_path = (
            Path(asn_database_path)
            if asn_database_path is not None
            else self._country_database_path.with_name(
                "GeoLite2-ASN.mmdb"
            )
        )

        self._country_reader: geoip2.database.Reader | None = None
        self._asn_reader: geoip2.database.Reader | None = None

        self._country_reader = self._open_database(
            self._country_database_path,
            database_name="Country",
        )

        self._asn_reader = self._open_database(
            self._asn_database_path,
            database_name="ASN",
        )

    @staticmethod
    def _open_database(
        database_path: Path,
        *,
        database_name: str,
    ) -> geoip2.database.Reader | None:
        """Abre una base MMDB sin impedir el inicio del sistema."""

        if not database_path.exists():
            logger.warning(
                "Base GeoIP %s no encontrada: %s",
                database_name,
                database_path,
            )
            return None

        try:
            return geoip2.database.Reader(database_path)

        except Exception:
            logger.exception(
                "No fue posible abrir la base GeoIP %s: %s",
                database_name,
                database_path,
            )
            return None

    def resolve(self, ip: str) -> GeoIPResult:
        """Obtiene país, ASN y proveedor asociados a una dirección IP."""

        try:
            address = ip_address(ip)
        except ValueError:
            return GeoIPResult()

        if address.is_private or address.is_loopback:
            return GeoIPResult()

        country_code: str | None = None
        country_name: str | None = None
        asn: int | None = None
        asn_organization: str | None = None

        if self._country_reader is not None:
            try:
                country_response = self._country_reader.country(ip)

                country_code = country_response.country.iso_code
                country_name = country_response.country.name

            except AddressNotFoundError:
                pass

            except Exception:
                logger.exception(
                    "Error resolviendo país para %s",
                    ip,
                )

        if self._asn_reader is not None:
            try:
                asn_response = self._asn_reader.asn(ip)

                asn = asn_response.autonomous_system_number
                asn_organization = (
                    asn_response.autonomous_system_organization
                )

            except AddressNotFoundError:
                pass

            except Exception:
                logger.exception(
                    "Error resolviendo ASN para %s",
                    ip,
                )

        return GeoIPResult(
            country_code=country_code,
            country_name=country_name,
            asn=asn,
            asn_organization=asn_organization,
        )

    def close(self) -> None:
        """Libera los lectores MMDB."""

        if self._country_reader is not None:
            self._country_reader.close()

        if self._asn_reader is not None:
            self._asn_reader.close()