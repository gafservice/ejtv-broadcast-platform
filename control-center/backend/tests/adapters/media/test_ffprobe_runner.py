import json
import subprocess

import pytest

from app.adapters.media.ffprobe_runner import FFprobeRunner


class Completed:
    def __init__(
        self,
        *,
        returncode=0,
        stdout="",
        stderr="",
    ):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_runner_executes_ffprobe_and_returns_json_payload() -> None:
    calls = []

    payload = {
        "streams": [
            {
                "codec_type": "video",
                "codec_name": "h264",
            }
        ]
    }

    def run(command, **kwargs):
        calls.append((command, kwargs))
        return Completed(
            stdout=json.dumps(payload),
        )

    runner = FFprobeRunner(
        executable="/usr/bin/ffprobe",
        timeout_seconds=8.0,
        run=run,
    )

    result = runner(
        "rtsp://127.0.0.1:8554/impact"
    )

    assert result == payload

    assert len(calls) == 1

    command, kwargs = calls[0]

    assert command == [
        "/usr/bin/ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_streams",
        "rtsp://127.0.0.1:8554/impact",
    ]

    assert kwargs["capture_output"] is True
    assert kwargs["text"] is True
    assert kwargs["timeout"] == 8.0
    assert kwargs["check"] is False


def test_runner_rejects_nonzero_ffprobe_return_code() -> None:
    def run(command, **kwargs):
        return Completed(
            returncode=1,
            stderr="physical probe failed",
        )

    runner = FFprobeRunner(
        run=run,
    )

    with pytest.raises(RuntimeError) as exc_info:
        runner("rtsp://example/impact")

    assert "physical probe failed" in str(
        exc_info.value
    )


def test_runner_rejects_invalid_json() -> None:
    def run(command, **kwargs):
        return Completed(
            stdout="not-json",
        )

    runner = FFprobeRunner(
        run=run,
    )

    with pytest.raises(ValueError):
        runner("rtsp://example/impact")


def test_runner_requires_json_object_payload() -> None:
    def run(command, **kwargs):
        return Completed(
            stdout='["not", "an", "object"]',
        )

    runner = FFprobeRunner(
        run=run,
    )

    with pytest.raises(TypeError):
        runner("rtsp://example/impact")


def test_runner_does_not_hide_timeout() -> None:
    def run(command, **kwargs):
        raise subprocess.TimeoutExpired(
            cmd=command,
            timeout=kwargs["timeout"],
        )

    runner = FFprobeRunner(
        timeout_seconds=3.0,
        run=run,
    )

    with pytest.raises(subprocess.TimeoutExpired):
        runner("rtsp://example/impact")


def test_runner_places_explicit_user_agent_before_rtsp_source() -> None:
    """Internal observer identity must be emitted as an input option."""
    calls = []

    def run(command, **kwargs):
        calls.append((command, kwargs))
        return Completed(
            stdout='{"streams":[]}',
        )

    runner = FFprobeRunner(
        executable="/usr/bin/ffprobe",
        timeout_seconds=8.0,
        user_agent="EBP-MediaObserver/1",
        run=run,
    )

    runner("rtsp://127.0.0.1:8554/impact")

    assert len(calls) == 1

    command, _ = calls[0]

    assert command == [
        "/usr/bin/ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_streams",
        "-user_agent",
        "EBP-MediaObserver/1",
        "rtsp://127.0.0.1:8554/impact",
    ]

    assert command[-3:] == [
        "-user_agent",
        "EBP-MediaObserver/1",
        "rtsp://127.0.0.1:8554/impact",
    ]
