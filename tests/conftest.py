from __future__ import annotations

import os
import tempfile
from collections.abc import Generator
from unittest.mock import patch

import pytest

MOCK_ENV = {
    "PAGERDUTY_TOKEN": "mock",
    "PAGERDUTY_EMAIL": "mock",
    "PAGERDUTY_TIMEOUT": "42",
}


@pytest.fixture(autouse=True)
def mock_environment_variables() -> Generator[None, None, None]:
    with patch.dict(os.environ, MOCK_ENV):
        yield None


@pytest.fixture
def mock_filename() -> Generator[str, None, None]:
    """Create tempfile, yield name for tests."""
    try:
        file_desc, path = tempfile.mkstemp(prefix="temp_", dir="tests/fixture")
        os.close(file_desc)
        yield path
    finally:
        os.remove(path)
