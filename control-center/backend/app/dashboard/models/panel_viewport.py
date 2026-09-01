"""Estado de navegación para colecciones visibles del dashboard."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PanelViewport:
    """Describe una ventana visible dentro de una colección ordenada."""

    offset: int = 0
    page_size: int = 5

    def __post_init__(self) -> None:
        if isinstance(self.offset, bool) or not isinstance(
            self.offset,
            int,
        ):
            raise TypeError(
                "offset must be an integer"
            )

        if self.offset < 0:
            raise ValueError(
                "offset must not be negative"
            )

        if isinstance(self.page_size, bool) or not isinstance(
            self.page_size,
            int,
        ):
            raise TypeError(
                "page_size must be an integer"
            )

        if self.page_size <= 0:
            raise ValueError(
                "page_size must be greater than zero"
            )

    def normalized_offset(
        self,
        total_items: int,
    ) -> int:
        """Retorna un offset válido para el tamaño actual."""

        self._validate_total_items(total_items)

        if total_items == 0:
            return 0

        maximum_offset = max(
            total_items - self.page_size,
            0,
        )

        return min(
            self.offset,
            maximum_offset,
        )

    def bounds(
        self,
        total_items: int,
    ) -> tuple[int, int]:
        """Retorna [inicio, fin) de la ventana visible."""

        start = self.normalized_offset(total_items)

        end = min(
            start + self.page_size,
            total_items,
        )

        return start, end

    def move(
        self,
        delta: int,
        *,
        total_items: int,
    ) -> "PanelViewport":
        """Desplaza la ventana una cantidad de filas."""

        self._validate_delta(delta)
        self._validate_total_items(total_items)

        maximum_offset = max(
            total_items - self.page_size,
            0,
        )

        new_offset = min(
            max(self.offset + delta, 0),
            maximum_offset,
        )

        return PanelViewport(
            offset=new_offset,
            page_size=self.page_size,
        )

    def page_up(
        self,
        *,
        total_items: int,
    ) -> "PanelViewport":
        """Retrocede una página."""

        return self.move(
            -self.page_size,
            total_items=total_items,
        )

    def page_down(
        self,
        *,
        total_items: int,
    ) -> "PanelViewport":
        """Avanza una página."""

        return self.move(
            self.page_size,
            total_items=total_items,
        )

    def home(self) -> "PanelViewport":
        """Mueve la ventana al inicio."""

        return PanelViewport(
            offset=0,
            page_size=self.page_size,
        )

    def end(
        self,
        *,
        total_items: int,
    ) -> "PanelViewport":
        """Mueve la ventana al último bloque disponible."""

        self._validate_total_items(total_items)

        return PanelViewport(
            offset=max(
                total_items - self.page_size,
                0,
            ),
            page_size=self.page_size,
        )

    @property
    def slice(self) -> slice:
        """Retorna el slice basado en el offset solicitado."""

        return slice(
            self.offset,
            self.offset + self.page_size,
        )

    @staticmethod
    def _validate_total_items(
        total_items: int,
    ) -> None:
        if isinstance(total_items, bool) or not isinstance(
            total_items,
            int,
        ):
            raise TypeError(
                "total_items must be an integer"
            )

        if total_items < 0:
            raise ValueError(
                "total_items must not be negative"
            )

    @staticmethod
    def _validate_delta(
        delta: int,
    ) -> None:
        if isinstance(delta, bool) or not isinstance(
            delta,
            int,
        ):
            raise TypeError(
                "delta must be an integer"
            )
