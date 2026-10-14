"""Contract: Live dimensions must reach run_once."""

from types import SimpleNamespace

import app.dashboard.application as application_module
from app.dashboard.application import DashboardApplication


def test_live_dimensions_are_forwarded_and_refreshed(monkeypatch):
    """Every iteration must use current Live console dimensions."""

    sizes = [(100, 30), (120, 40)]
    received = []

    class FakeLive:
        def __init__(self, *args, **kwargs):
            self.console = SimpleNamespace(
                size=SimpleNamespace(width=100, height=30)
            )

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def update(self, renderable, *, refresh):
            assert refresh is True

            if len(received) == 1:
                self.console.size = SimpleNamespace(
                    width=120,
                    height=40,
                )

    application = object.__new__(DashboardApplication)

    application._keyboard_input = None
    application._key_parser = None

    def fake_run_once(
        *,
        terminal_width=None,
        incoming_height=None,
    ):
        received.append((terminal_width, incoming_height))
        return object()

    monkeypatch.setattr(
        application_module,
        "Live",
        FakeLive,
    )

    monkeypatch.setattr(
        application,
        "run_once",
        fake_run_once,
    )

    application.run(
        refresh_interval_seconds=0,
        max_iterations=2,
    )

    assert len(received) == 2

    assert received[0] == (100, 7)
    assert received[1] == (120, 17)
