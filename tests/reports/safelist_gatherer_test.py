"""Tests for sample"""
from __future__ import annotations

import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from pd_utils.reports import safelist_gatherer as pdip

EU_SAMPLE = Path("tests/fixture/safelist_gatherer/sample_eu.json").read_text()
US_SAMPLE = Path("tests/fixture/safelist_gatherer/sample_us.json").read_text()

EXPECTED_US_IPS = set(json.loads(US_SAMPLE))
EXPECTED_EU_IPS = set(json.loads(EU_SAMPLE))


@pytest.mark.parametrize(
    ("url", "route", "expected"),
    (
        (
            "raw.githubusercontent.com",
            "/Preocts/pd-utils/main/README.md",
            True,
        ),
        (
            "raw.githubusercontent.com",
            "/Preocts/pd-utils/main/not_there.md",
            False,
        ),
    ),
)
def test_get_url_page(url: str, route: str, expected: bool) -> None:
    result = pdip._get_url_page(url, route)

    assert bool(result) is expected


@pytest.mark.parametrize(
    ("func", "resp", "expected"),
    (
        (
            pdip.get_all_safelist,
            [US_SAMPLE, EU_SAMPLE, US_SAMPLE, EU_SAMPLE],
            EXPECTED_US_IPS.union(EXPECTED_EU_IPS),
        ),
        (
            pdip.get_us_safelist,
            [US_SAMPLE, US_SAMPLE],
            EXPECTED_US_IPS,
        ),
        (
            pdip.get_eu_safelist,
            [EU_SAMPLE, EU_SAMPLE],
            EXPECTED_EU_IPS,
        ),
    ),
)
def test_get_safelists(func: Any, resp: list[str], expected: set[str]) -> None:

    with patch.object(pdip, "_get_url_page", side_effect=resp):
        result = func()

    assert len(result - expected) == 0


def test_console_out() -> None:
    resps = [US_SAMPLE, EU_SAMPLE, US_SAMPLE, EU_SAMPLE]
    expected = EXPECTED_US_IPS.union(EXPECTED_EU_IPS)

    with patch.object(pdip, "_get_url_page", side_effect=resps):
        with redirect_stdout(StringIO()) as con_cap:

            result = pdip.console_output()

            clean_capture = {line for line in con_cap.getvalue().split("\n") if line}

    assert result == 0
    assert len(clean_capture - expected) == 0
