from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock

import pytest
from _pytest.monkeypatch import MonkeyPatch

from pd_utils.util import datetool

MOCK_NOW = datetime(2022, 12, 25, 13, 50, 30, 0)
MOCK_ISO = "2022-12-25T13:50:30Z"


@pytest.fixture
def patch_datetime_utcnow(monkeypatch: MonkeyPatch) -> None:
    mock_dt = MagicMock(utcnow=MagicMock(return_value=MOCK_NOW))

    monkeypatch.setattr(datetool, "datetime", mock_dt)


def test_to_isotime() -> None:
    result = datetool.to_isotime(MOCK_NOW)

    assert result == MOCK_ISO


def test_to_datetime() -> None:
    result = datetool.to_datetime(MOCK_ISO)

    assert result == MOCK_NOW
    assert result.tzinfo is None


def test_utcnow_isotime(patch_datetime_utcnow: None) -> None:

    result = datetool.utcnow_isotime()

    assert result == MOCK_ISO


def test_add_offset() -> None:
    expected = "2022-12-26T14:51:31Z"

    result = datetool.add_offset(MOCK_ISO, days=1, hours=1, minutes=1, seconds=1)

    assert result == expected


@pytest.mark.parametrize(
    ("time_slots", "expected"),
    (
        (
            [
                ("2022-07-30T12:30:00Z", "2022-07-31T00:00:00Z"),
                ("2022-07-30T00:00:00Z", "2022-07-30T12:00:00Z"),
                ("2022-07-29T12:30:00Z", "2022-07-30T00:00:00Z"),
                ("2022-07-29T04:18:19Z", "2022-07-29T12:00:00Z"),
            ],
            False,
        ),
        (
            [
                ("2022-07-30T12:00:00Z", "2022-07-31T00:00:00Z"),
                ("2022-07-30T00:00:00Z", "2022-07-30T12:00:00Z"),
                ("2022-07-29T12:00:00Z", "2022-07-30T00:00:00Z"),
                ("2022-07-29T04:18:19Z", "2022-07-29T12:00:00Z"),
            ],
            True,
        ),
        (
            [],
            False,
        ),
    ),
)
def test_is_gapless(time_slots: list[tuple[str, str]], expected: bool) -> None:
    assert datetool._is_gapless(time_slots) is expected


@pytest.mark.parametrize(
    ("time_slots", "start", "stop", "expected"),
    (
        (  # Test: Has gaps
            [
                ("2022-07-29T04:18:19Z", "2022-07-29T12:00:00Z"),
                ("2022-07-30T00:00:00Z", "2022-07-30T12:00:00Z"),
                ("2022-07-29T12:30:00Z", "2022-07-30T00:00:00Z"),
                ("2022-07-30T12:30:00Z", "2022-07-31T00:00:00Z"),
            ],
            "2022-07-29T04:18:19Z",
            "2022-07-31T00:00:00Z",
            False,
        ),
        (  # Test: No gaps, missing start coverage
            [
                ("2022-07-29T04:18:19Z", "2022-07-29T12:00:00Z"),
                ("2022-07-30T00:00:00Z", "2022-07-30T12:00:00Z"),
                ("2022-07-29T12:00:00Z", "2022-07-30T00:00:00Z"),
                ("2022-07-30T12:00:00Z", "2022-07-31T00:00:00Z"),
            ],
            "2022-07-29T04:17:19Z",
            "2022-07-31T00:00:00Z",
            False,
        ),
        (  # Test: No gaps, missing end coverage
            [
                ("2022-07-29T04:18:19Z", "2022-07-29T12:00:00Z"),
                ("2022-07-30T00:00:00Z", "2022-07-30T12:00:00Z"),
                ("2022-07-29T12:00:00Z", "2022-07-30T00:00:00Z"),
                ("2022-07-30T12:00:00Z", "2022-07-31T00:00:00Z"),
            ],
            "2022-07-29T04:18:19Z",
            "2022-08-01T00:00:00Z",
            False,
        ),
        (  # Test: No gaps, full coverage
            [
                ("2022-07-29T04:18:19Z", "2022-07-29T12:00:00Z"),
                ("2022-07-29T04:18:19Z", "2022-07-30T00:00:00Z"),
                ("2022-07-30T00:00:00Z", "2022-07-30T12:00:00Z"),
                ("2022-07-30T12:00:00Z", "2022-07-31T00:00:00Z"),
                ("2022-07-31T00:00:00Z", "2022-07-31T12:00:00Z"),
                ("2022-07-31T12:00:00Z", "2022-08-01T00:00:00Z"),
            ],
            "2022-07-29T04:18:19Z",
            "2022-08-01T00:00:00Z",
            True,
        ),
        (  # Test: Edge case, this actually should never happen
            [],
            "2022-07-29T04:18:19Z",
            "2022-08-01T00:00:00Z",
            False,
        ),
    ),
)
def test_is_covered(
    time_slots: list[tuple[str, str]],
    start: str,
    stop: str,
    expected: bool,
) -> None:
    assert datetool.is_covered(time_slots, start, stop) is expected


@pytest.mark.parametrize(
    ("from_", "to_", "expected"),
    (
        ("2022-12-25T13:50:30Z", "2022-12-25T13:51:00Z", 30),
        ("2022-12-25T13:50:30Z", "2022-12-26T13:49:30Z", 86_340),
        ("2022-12-25T13:50:30Z", "2022-12-26T13:51:30Z", 86_460),
        ("2022-12-25T13:50:30Z", "2022-12-26T13:50:30Z", 86_400),
        ("2022-12-25T13:50:30Z", "2022-12-25T13:50:30Z", 0),
    ),
)
def test_to_seconds(from_: str, to_: str, expected: int) -> None:
    result = datetool.to_seconds(from_, to_)

    assert result == expected
