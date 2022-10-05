from __future__ import annotations

import os
import tempfile
from collections.abc import Generator

import pytest


@pytest.fixture
def mock_filename() -> Generator[str, None, None]:
    """Create tempfile, yield name for tests."""
    try:
        file_desc, path = tempfile.mkstemp(prefix="temp_", dir="tests/fixture")
        os.close(file_desc)
        yield path
    finally:
        os.remove(path)
