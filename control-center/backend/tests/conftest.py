"""Global pytest isolation for Control Center tests."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


# Configure the NOC runtime-owner namespace before test modules import
# app.main.  TestClient executes the real application lifespan, so its
# ownership lock must not contend with a concurrently running Control
# Center process.
_TEST_RUNTIME_LOCK_ROOT = (
    Path(tempfile.gettempdir())
    / f"ejtv-control-center-pytest-{os.getpid()}"
)

os.environ["NOC_RUNTIME_LOCK_PATH"] = str(
    _TEST_RUNTIME_LOCK_ROOT
)
