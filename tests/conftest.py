from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ncp.core.runtime import Runtime, build_default_universe  # noqa: E402
from ncp.utils.config import Config  # noqa: E402


@pytest.fixture
def runtime(tmp_path) -> Runtime:
    """A runtime that persists to a temp dir instead of ncp_output/."""
    return Runtime(build_default_universe(), config=Config(output_dir=str(tmp_path / "out")))
