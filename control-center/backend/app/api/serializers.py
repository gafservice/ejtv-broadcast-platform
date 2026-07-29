"""
Utilidades para serializar modelos del dominio.

Convierte dataclasses y estructuras anidadas en objetos
compatibles con JSON.
"""

from dataclasses import asdict
from dataclasses import is_dataclass
from typing import Any


def serialize(value: Any) -> Any:
    """
    Convierte recursivamente objetos del dominio
    en estructuras serializables por FastAPI.
    """

    if is_dataclass(value):
        return {
            key: serialize(val)
            for key, val in asdict(value).items()
        }

    if isinstance(value, dict):
        return {
            key: serialize(val)
            for key, val in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [
            serialize(item)
            for item in value
        ]

    return value