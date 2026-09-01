"""Pruebas del adaptador POSIX de teclado."""

from unittest.mock import Mock, patch

from app.dashboard.services.posix_keyboard_input import (
    PosixKeyboardInput,
)


def test_non_tty_stream_remains_inactive() -> None:
    stream = Mock()
    stream.isatty.return_value = False

    keyboard = PosixKeyboardInput(stream)

    with keyboard:
        assert keyboard.active is False

    stream.fileno.assert_not_called()


def test_enter_enables_cbreak_mode() -> None:
    stream = Mock()
    stream.isatty.return_value = True
    stream.fileno.return_value = 7

    original_settings = ["original"]

    with (
        patch(
            "app.dashboard.services.posix_keyboard_input."
            "termios.tcgetattr",
            return_value=original_settings,
        ) as tcgetattr,
        patch(
            "app.dashboard.services.posix_keyboard_input."
            "tty.setcbreak",
        ) as setcbreak,
        patch(
            "app.dashboard.services.posix_keyboard_input."
            "termios.tcsetattr",
        ),
    ):
        keyboard = PosixKeyboardInput(stream)

        keyboard.__enter__()

        assert keyboard.active is True
        tcgetattr.assert_called_once_with(7)
        setcbreak.assert_called_once_with(7)

        keyboard.close()


def test_close_restores_terminal_settings() -> None:
    stream = Mock()
    stream.isatty.return_value = True
    stream.fileno.return_value = 9

    original_settings = ["saved"]

    with (
        patch(
            "app.dashboard.services.posix_keyboard_input."
            "termios.tcgetattr",
            return_value=original_settings,
        ),
        patch(
            "app.dashboard.services.posix_keyboard_input."
            "tty.setcbreak",
        ),
        patch(
            "app.dashboard.services.posix_keyboard_input."
            "termios.tcsetattr",
        ) as tcsetattr,
    ):
        keyboard = PosixKeyboardInput(stream)

        keyboard.__enter__()
        keyboard.close()

        tcsetattr.assert_called_once_with(
            9,
            1,
            original_settings,
        )

        assert keyboard.active is False


def test_context_manager_restores_terminal() -> None:
    stream = Mock()
    stream.isatty.return_value = True
    stream.fileno.return_value = 11

    with (
        patch(
            "app.dashboard.services.posix_keyboard_input."
            "termios.tcgetattr",
            return_value=["saved"],
        ),
        patch(
            "app.dashboard.services.posix_keyboard_input."
            "tty.setcbreak",
        ),
        patch(
            "app.dashboard.services.posix_keyboard_input."
            "termios.tcsetattr",
        ) as tcsetattr,
    ):
        keyboard = PosixKeyboardInput(stream)

        with keyboard:
            assert keyboard.active is True

        assert keyboard.active is False
        tcsetattr.assert_called_once()


def test_read_available_returns_none_when_inactive() -> None:
    keyboard = PosixKeyboardInput(Mock())

    assert keyboard.read_available() is None


def test_read_available_returns_none_without_data() -> None:
    stream = Mock()
    stream.isatty.return_value = True
    stream.fileno.return_value = 13

    with (
        patch(
            "app.dashboard.services.posix_keyboard_input."
            "termios.tcgetattr",
            return_value=["saved"],
        ),
        patch(
            "app.dashboard.services.posix_keyboard_input."
            "tty.setcbreak",
        ),
        patch(
            "app.dashboard.services.posix_keyboard_input."
            "termios.tcsetattr",
        ),
        patch(
            "app.dashboard.services.posix_keyboard_input."
            "select.select",
            return_value=([], [], []),
        ),
    ):
        keyboard = PosixKeyboardInput(stream)
        keyboard.__enter__()

        assert keyboard.read_available() is None

        keyboard.close()


def test_read_available_returns_bytes() -> None:
    stream = Mock()
    stream.isatty.return_value = True
    stream.fileno.return_value = 15

    with (
        patch(
            "app.dashboard.services.posix_keyboard_input."
            "termios.tcgetattr",
            return_value=["saved"],
        ),
        patch(
            "app.dashboard.services.posix_keyboard_input."
            "tty.setcbreak",
        ),
        patch(
            "app.dashboard.services.posix_keyboard_input."
            "termios.tcsetattr",
        ),
        patch(
            "app.dashboard.services.posix_keyboard_input."
            "select.select",
            return_value=([15], [], []),
        ),
        patch(
            "app.dashboard.services.posix_keyboard_input."
            "os.read",
            return_value=b"\x1b[B",
        ) as os_read,
    ):
        keyboard = PosixKeyboardInput(stream)
        keyboard.__enter__()

        assert keyboard.read_available() == b"\x1b[B"

        os_read.assert_called_once_with(
            15,
            32,
        )

        keyboard.close()


def test_close_is_idempotent() -> None:
    keyboard = PosixKeyboardInput(Mock())

    keyboard.close()
    keyboard.close()

    assert keyboard.active is False
