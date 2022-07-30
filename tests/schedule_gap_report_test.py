from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from httpx import Response

from pd_util_scripts.schedule_gap_report import CoverageGapReport
from pd_util_scripts.schedule_gap_report import QueryError

SCHEDULES_RESP = Path("tests/fixture/cov_gap/schedule_list.json").read_text()
EXPECTED_IDS = {"PG3MDI8", "P4TPEME"}

SCHEDULE_RESP = Path("tests/fixture/cov_gap/schedule_gap.json").read_text()
EXPECTED_ID = "PG3MDI8"


@pytest.fixture
def search() -> CoverageGapReport:
    return CoverageGapReport("mock", max_query_limit=1, look_ahead_days=14)


def test_get_all_schedule_ids(search: CoverageGapReport) -> None:
    resp_jsons = json.loads(SCHEDULES_RESP)
    resps = [Response(200, content=json.dumps(resp)) for resp in resp_jsons]
    with patch.object(search._http, "get", side_effect=resps):

        results = search._get_all_schedule_ids()

    assert not results - EXPECTED_IDS


def test_get_all_schedules_error(search: CoverageGapReport) -> None:
    resps = [Response(401, content="")]

    with patch.object(search._http, "get", side_effect=resps):

        with pytest.raises(QueryError):

            search._get_all_schedule_ids()


def test_get_schedule_coverage(search: CoverageGapReport) -> None:
    resps = [Response(200, content=SCHEDULE_RESP)]
    with patch.object(search._http, "get", side_effect=resps):

        result = search.get_schedule_coverage("mock")

    assert result is not None
    assert result.pd_id == EXPECTED_ID


def test_get_schedule_coverage_fails(search: CoverageGapReport) -> None:
    resps = [Response(401, content="Failure")]
    with patch.object(search._http, "get", side_effect=resps):

        result = search.get_schedule_coverage("mock")

    assert result is None


def test_get_schedule_coverages(search: CoverageGapReport) -> None:
    mock_ids = ["a", "b", "c"]
    resps = ["Good", "Better", None]

    with patch.object(search, "get_schedule_coverage", side_effect=resps):

        results = search._get_schedule_coverages(mock_ids)  # type: ignore

    assert len(results) == 2
    assert "c" not in results
