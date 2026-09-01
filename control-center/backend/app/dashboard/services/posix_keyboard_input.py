"""Entrada de teclado POSIX no bloqueante para el dashboard."""

from __future__ import annotations

import os
import select
import sys
import termios
import tty
from types import TracebackType
from typing import IO


class PosixKeyboardInput:
    """Lee secuencias del terminal sin bloquear el dashboard."""

    def __init__(
        self,
        stream: IO[str] | None = None,
    ) -> None:
        self._stream = stream if stream is not None else sys.stdin
        self._fd: int | None = None
        self._original_settings: list | None = None
        self._active = False

    @property
    def active(self) -> bool:
        return self._active

    def __enter__(self) -> "PosixKeyboardInput":
        if self._active:
            return self

        if not self._stream.isatty():
            return self

        fd = self._stream.fileno()
        original_settings = termios.tcgetattr(fd)

        tty.setcbreak(fd)

        self._fd = fd
        self._original_settings = original_settings
        self._active = True

        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        if not self._active:
            return

        if (
            self._fd is not None
            and self._original_settings is not None
        ):
            termios.tcsetattr(
                self._fd,
                termios.TCSADRAIN,
                self._original_settings,
            )

        self._fd = None
        self._original_settings = None
        self._active = False

    def read_available(
        self,
        *,
        timeout_seconds: float = 0.0,
    ) -> bytes | None:
        """Lee una secuencia disponible dentro del timeout indicado."""

        if isinstance(timeout_seconds, bool) or not isinstance(
            timeout_seconds,
            (int, float),
        ):
            raise TypeError(
                "timeout_seconds must be a number"
            )

        if timeout_seconds < 0:
            raise ValueError(
                "timeout_seconds must be greater than or equal to zero"
            )

        if not self._active or self._fd is None:
            return None

        ready, _, _ = select.select(
            [self._fd],
            [],
            [],
            float(timeout_seconds),
        )

        if not ready:
            return None

        data = os.read(
            self._fd,
            32,
        )

        return data or None
