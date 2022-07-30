from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock

import pytest
from _pytest.monkeypatch import MonkeyPatch

from pd_util_scripts.util import date_tool
from pd_util_scripts.util import DateTool

MOCK_NOW = datetime(2022, 12, 25, 13, 50, 30, 0)
MOCK_ISO = "2022-12-25T13:50:30Z"


@pytest.fixture
def patch_datetime_utcnow(monkeypatch: MonkeyPatch) -> None:
    mock_dt = MagicMock(utcnow=MagicMock(return_value=MOCK_NOW))

    monkeypatch.setattr(date_tool, "datetime", mock_dt)


def test_to_isotime() -> None:
    result = DateTool.to_isotime(MOCK_NOW)

    assert result == MOCK_ISO


def test_utcnow_isotime(patch_datetime_utcnow: None) -> None:

    result = date_tool.DateTool.utcnow_isotime()

    assert result == MOCK_ISO


def test_add_offset() -> None:
    expected = "2022-12-26T14:51:31Z"

    result = DateTool.add_offset(MOCK_ISO, days=1, hours=1, minutes=1, seconds=1)

    assert result == expected
