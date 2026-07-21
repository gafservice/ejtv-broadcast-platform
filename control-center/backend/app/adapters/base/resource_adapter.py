"""Contrato común para adaptadores de recursos monitoreados."""

from __future__ import annotations

from typing import Generic, Protocol, TypeVar, runtime_checkable


SnapshotT = TypeVar("SnapshotT")


@runtime_checkable
class ResourceAdapter(Protocol, Generic[SnapshotT]):
    """Contrato mínimo de cualquier recurso supervisado.

    Un adaptador debe poder comprobar su disponibilidad y generar una
    representación puntual del estado del recurso.
    """

    def health(self) -> bool:
        """Indica si el recurso está disponible."""
        ...

    def get_snapshot(self) -> SnapshotT:
        """Obtiene el estado normalizado del recurso."""
        ...
