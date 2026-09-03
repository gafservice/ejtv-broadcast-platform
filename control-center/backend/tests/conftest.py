"""Global pytest isolation for Control Center tests."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


# Configure the complete NOC persistence/ownership namespace before test
# modules import app.main. TestClient executes the real application lifespan,
# so tests must never contend with or write into a concurrently running
# Control Center runtime.
_TEST_NOC_ROOT = (
    Path(tempfile.gettempdir())
    / f"ejtv-control-center-pytest-{os.getpid()}"
)

os.environ["NOC_RUNTIME_LOCK_PATH"] = str(
    _TEST_NOC_ROOT / "runtime-locks"
)

os.environ["NOC_HISTORY_DATABASE_PATH"] = str(
    _TEST_NOC_ROOT / "noc-history.db"
)

os.environ["NOC_EVIDENCE_PATH"] = str(
    _TEST_NOC_ROOT / "noc-evidence"
)
