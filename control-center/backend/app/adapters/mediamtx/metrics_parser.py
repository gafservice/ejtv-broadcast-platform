"""Parser mínimo para métricas Prometheus de MediaMTX."""

from __future__ import annotations

import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from .exceptions import MediaMTXInvalidResponseError


_METRIC_LINE_PATTERN = re.compile(
    r"^(?P<name>[a-zA-Z_:][a-zA-Z0-9_:]*)"
    r"(?:\{(?P<labels>.*)\})?"
    r"\s+"
    r"(?P<value>"
    r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)"
    r"(?:[eE][+-]?\d+)?"
    r"|NaN|[+-]Inf"
    r")"
    r"(?:\s+\d+)?$"
)

_LABEL_PATTERN = re.compile(
    r'(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)='
    r'"(?P<value>(?:\\.|[^"\\])*)"'
)


@dataclass(frozen=True, slots=True)
class PrometheusSample:
    """Una muestra individual del documento Prometheus."""

    name: str
    labels: Mapping[str, str]
    value: float

    def has_labels(self, **expected: str) -> bool:
        """Indica si contiene todas las etiquetas solicitadas."""
        return all(
            self.labels.get(name) == value
            for name, value in expected.items()
        )


@dataclass(frozen=True, slots=True)
class MediaMTXMetricsSnapshot:
    """Conjunto inmutable de métricas obtenidas de MediaMTX."""

    samples: tuple[PrometheusSample, ...]

    def find(
        self,
        metric_name: str,
        **labels: str,
    ) -> tuple[PrometheusSample, ...]:
        """Busca muestras por nombre y etiquetas."""
        return tuple(
            sample
            for sample in self.samples
            if sample.name == metric_name
            and sample.has_labels(**labels)
        )

    def get_value(
        self,
        metric_name: str,
        *,
        default: float | None = None,
        **labels: str,
    ) -> float | None:
        """Obtiene un único valor o el valor predeterminado."""
        matches = self.find(metric_name, **labels)

        if not matches:
            return default

        if len(matches) > 1:
            raise MediaMTXInvalidResponseError(
                "La métrica "
                f"{metric_name!r} produjo más de una coincidencia."
            )

        return matches[0].value


class MediaMTXMetricsParser:
    """Convierte texto Prometheus en objetos del dominio del adaptador."""

    def parse(self, metrics_text: str) -> MediaMTXMetricsSnapshot:
        """Procesa un documento Prometheus completo."""
        samples: list[PrometheusSample] = []

        for line_number, raw_line in enumerate(
            metrics_text.splitlines(),
            start=1,
        ):
            line = raw_line.strip()

            if not line or line.startswith("#"):
                continue

            match = _METRIC_LINE_PATTERN.fullmatch(line)

            if match is None:
                raise MediaMTXInvalidResponseError(
                    "Línea Prometheus inválida "
                    f"en posición {line_number}: {line!r}"
                )

            labels = self._parse_labels(
                match.group("labels") or "",
                line_number=line_number,
            )

            try:
                value = float(match.group("value"))
            except ValueError as exc:
                raise MediaMTXInvalidResponseError(
                    "Valor Prometheus inválido "
                    f"en línea {line_number}."
                ) from exc

            samples.append(
                PrometheusSample(
                    name=match.group("name"),
                    labels=MappingProxyType(labels),
                    value=value,
                )
            )

        if not samples:
            raise MediaMTXInvalidResponseError(
                "El documento Prometheus no contiene muestras."
            )

        return MediaMTXMetricsSnapshot(samples=tuple(samples))

    @staticmethod
    def _parse_labels(
        labels_text: str,
        *,
        line_number: int,
    ) -> dict[str, str]:
        """Procesa las etiquetas de una muestra."""
        if not labels_text:
            return {}

        labels: dict[str, str] = {}
        position = 0

        while position < len(labels_text):
            match = _LABEL_PATTERN.match(labels_text, position)

            if match is None:
                raise MediaMTXInvalidResponseError(
                    "Etiquetas Prometheus inválidas "
                    f"en línea {line_number}."
                )

            name = match.group("name")
            value = (
                match.group("value")
                .replace(r"\\", "\\")
                .replace(r"\"", '"')
                .replace(r"\n", "\n")
            )

            labels[name] = value
            position = match.end()

            if position == len(labels_text):
                break

            if labels_text[position] != ",":
                raise MediaMTXInvalidResponseError(
                    "Separador de etiquetas inválido "
                    f"en línea {line_number}."
                )

            position += 1

        return labels
