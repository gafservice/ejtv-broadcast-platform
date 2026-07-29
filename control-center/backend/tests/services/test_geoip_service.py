"""Pruebas del servicio local de resolución GeoIP."""

from __future__ import annotations

from types import SimpleNamespace

from geoip2.errors import AddressNotFoundError

from app.services.geoip_service import (
    GeoIPResult,
    GeoIPService,
)


class FakeReader:
    """Lector MMDB simulado para pruebas unitarias."""

    def __init__(
        self,
        *,
        country_code: str | None = "CR",
        country_name: str | None = "Costa Rica",
        error: Exception | None = None,
    ) -> None:
        self.country_code = country_code
        self.country_name = country_name
        self.error = error
        self.requested_ips: list[str] = []
        self.closed = False

    def country(self, ip: str) -> SimpleNamespace:
        """Simula una consulta por país."""

        self.requested_ips.append(ip)

        if self.error is not None:
            raise self.error

        return SimpleNamespace(
            country=SimpleNamespace(
                iso_code=self.country_code,
                name=self.country_name,
            )
        )

    def close(self) -> None:
        """Registra el cierre del lector."""

        self.closed = True


def build_service_with_readers(
    country_reader: FakeReader | None = None,
    asn_reader: FakeReader | None = None,
) -> GeoIPService:
    service = GeoIPService.__new__(GeoIPService)

    service._country_reader = country_reader
    service._asn_reader = asn_reader

    return service


def test_geoip_result_defaults_to_unknown() -> None:
    result = GeoIPResult()

    assert result.country_code is None
    assert result.country_name is None


def test_resolve_public_ip_returns_country() -> None:
    reader = FakeReader()
    service = build_service_with_readers(
        country_reader=reader,
    )

    result = service.resolve("8.8.8.8")

    assert result == GeoIPResult(
        country_code="CR",
        country_name="Costa Rica",
    )
    assert reader.requested_ips == ["8.8.8.8"]


def test_resolve_private_ip_skips_reader() -> None:
    reader = FakeReader()
    service = build_service_with_readers(reader)

    result = service.resolve("192.168.1.10")

    assert result == GeoIPResult()
    assert reader.requested_ips == []


def test_resolve_loopback_ip_skips_reader() -> None:
    reader = FakeReader()
    service = build_service_with_readers(reader)

    result = service.resolve("127.0.0.1")

    assert result == GeoIPResult()
    assert reader.requested_ips == []


def test_resolve_invalid_ip_returns_unknown() -> None:
    reader = FakeReader()
    service = build_service_with_readers(reader)

    result = service.resolve("not-an-ip")

    assert result == GeoIPResult()
    assert reader.requested_ips == []


def test_resolve_without_reader_returns_unknown() -> None:
    service = build_service_with_readers()

    result = service.resolve("8.8.8.8")

    assert result == GeoIPResult()


def test_resolve_unknown_public_ip_returns_unknown() -> None:
    reader = FakeReader(
        error=AddressNotFoundError("not found"),
    )
    service = build_service_with_readers(reader)

    result = service.resolve("8.8.8.8")

    assert result == GeoIPResult()


def test_resolve_reader_error_returns_unknown() -> None:
    reader = FakeReader(
        error=RuntimeError("database failure"),
    )
    service = build_service_with_readers(reader)

    result = service.resolve("8.8.8.8")

    assert result == GeoIPResult()


def test_close_closes_reader() -> None:
    reader = FakeReader()
    service = build_service_with_readers(reader)

    service.close()

    assert reader.closed is True


def test_close_without_reader_does_not_fail() -> None:
    service = build_service_with_readers(None)

    service.close()