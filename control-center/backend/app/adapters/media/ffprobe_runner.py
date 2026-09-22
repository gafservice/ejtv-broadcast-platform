"""Physical ffprobe execution boundary for media observation."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from typing import Any


Run = Callable[..., Any]


class FFprobeRunner:
    """Execute ffprobe and return its JSON object payload."""

    def __init__(
        self,
        *,
        executable: str = "/usr/bin/ffprobe",
        timeout_seconds: float = 8.0,
        run: Run = subprocess.run,
    ) -> None:
        if not executable:
            raise ValueError("executable must not be empty")

        if timeout_seconds <= 0:
            raise ValueError(
                "timeout_seconds must be positive"
            )

        if not callable(run):
            raise TypeError("run must be callable")

        self._executable = executable
        self._timeout_seconds = timeout_seconds
        self._run = run

    def __call__(
        self,
        source: str,
    ) -> dict[str, Any]:
        if not source:
            raise ValueError("source must not be empty")

        command = [
            self._executable,
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_streams",
            source,
        ]

        result = self._run(
            command,
            capture_output=True,
            text=True,
            timeout=self._timeout_seconds,
            check=False,
        )

        if result.returncode != 0:
            detail = (result.stderr or "").strip()

            if detail:
                raise RuntimeError(
                    f"ffprobe failed: {detail}"
                )

            raise RuntimeError(
                "ffprobe failed with "
                f"return code {result.returncode}"
            )

        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "ffprobe returned invalid JSON"
            ) from exc

        if not isinstance(payload, dict):
            raise TypeError(
                "ffprobe JSON payload must be an object"
            )

        return payload
